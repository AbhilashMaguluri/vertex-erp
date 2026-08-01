"""Vertex Core — the request pipeline.

Every request runs every stage, in this order, with no bypass:

    1  Goal Builder          what is the user trying to accomplish?
    2  Context Builder       who are they, where are they, what is in view?
    3  Input Guardrails      injection, jailbreak, spoofing, invalid input
    4  Intent Detection      which capability class handles this?
    5  Planner               respond / execute / clarify / reject
    6  Permission Validation user, role, ownership, action — before anything runs
    7  Tool Selection        resolved from the registry by capability
    8  Tool Execution        the tool changes state, never the model
    9  LLM Reasoning         communicate the outcome
    10 Output Guardrails     leaks and fabricated records, before delivery
    11 Evaluation            score the interaction
    12 Final Response

Stages 1–8 finish before the model is invoked. That ordering is the whole
design: the model reports decisions, it does not make them.

Streaming and output guardrails are reconciled by holding back a tail window.
Tokens are released only once enough following text exists to judge them, and
if a violation still surfaces the stream is cut and a ``replace`` event tells
the client to swap the partial message for a safe one.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import AsyncGenerator, List, Optional

from app.ai.core.context_builder import ContextBuilder
from app.ai.core.evaluation import EvaluationInput, Evaluator
from app.ai.core.goal import GoalBuilder
from app.ai.core.guardrails import GuardrailResult, InputGuardrails, OutputGuardrails
from app.ai.core.intent import IntentDetector, create_default_detector
from app.ai.core.logging import PipelineLogger
from app.ai.core.permissions import PermissionDecision, PermissionValidator
from app.ai.core.planner import Planner
from app.ai.core.ownership import DataOwnershipResolver
from app.ai.models.context import VertexContext
from app.ai.models.evaluation import StageTimings
from app.ai.models.goal import Goal, GoalType
from app.ai.models.intent import DetectedIntent
from app.ai.models.plan import ExecutionPlan, PlanAction
from app.ai.models.request import VertexRequest
from app.ai.observability.store import evaluation_store
from app.ai.prompts.builder import (
    build_data_answer_chain,
    build_prompt_chain,
    build_tool_confirmation_chain,
    build_tool_failure_chain,
)
from app.ai.providers.base import AIProvider, get_provider
from app.ai.tools.base import ToolExecutionContext, ToolRegistry, ToolResult
from app.ai.tools.registry_setup import get_registry

logger = logging.getLogger(__name__)

#: Control markers the router converts into typed SSE events.
ACTION_MARKER = "__SSE_ACTION__"
REPLACE_MARKER = "__SSE_REPLACE__"

#: Characters withheld from the stream so the output guardrail can inspect
#: text before the user sees it. Comfortably longer than any pattern it
#: matches, short enough to be imperceptible while typing out.
_GUARD_WINDOW = 180


class VertexCore:
    """Orchestrates the agent pipeline for one request at a time."""

    def __init__(
        self,
        provider: Optional[AIProvider] = None,
        db: Optional[object] = None,
        auth_user: Optional[object] = None,
        tools: Optional[ToolRegistry] = None,
        goal_builder: Optional[GoalBuilder] = None,
        context_builder: Optional[ContextBuilder] = None,
        intent_detector: Optional[IntentDetector] = None,
        planner: Optional[Planner] = None,
        ownership: Optional[DataOwnershipResolver] = None,
        permissions: Optional[PermissionValidator] = None,
        input_guardrails: Optional[InputGuardrails] = None,
        output_guardrails: Optional[OutputGuardrails] = None,
        evaluator: Optional[Evaluator] = None,
    ) -> None:
        # A missing API key must not take down the pipeline: guardrails,
        # permissions and tools all work without a model, and a tool-only
        # request should still succeed. The failure surfaces at generation.
        self._provider = provider or _safe_provider()
        self._db = db
        self._auth_user = auth_user

        self._tools = tools or get_registry()
        self._goal_builder = goal_builder or GoalBuilder(self._provider)
        self._context_builder = context_builder or ContextBuilder(db)
        self._intent_detector = intent_detector or create_default_detector(self._provider)
        self._planner = planner or Planner()
        self._ownership = ownership or DataOwnershipResolver()
        self._permissions = permissions or PermissionValidator()
        self._input_guardrails = input_guardrails or InputGuardrails()
        self._output_guardrails = output_guardrails or OutputGuardrails()
        self._evaluator = evaluator or Evaluator()

    # ------------------------------------------------------------------

    async def process(self, request: VertexRequest) -> AsyncGenerator[str, None]:
        """Run the pipeline, yielding response text and control markers."""
        request_id = str(uuid.uuid4())[:8]
        log = PipelineLogger(request_id=request_id)

        # State the evaluation stage reads, regardless of where we exit.
        context: Optional[VertexContext] = None
        goal: Optional[Goal] = None
        intent: Optional[DetectedIntent] = None
        plan: Optional[ExecutionPlan] = None
        input_guard: Optional[GuardrailResult] = None
        output_guard: Optional[GuardrailResult] = None
        permission: Optional[PermissionDecision] = None
        tool_results: List[ToolResult] = []
        response = ""
        fallback_used = False
        error: Optional[str] = None
        user_message = ""

        try:
            if not request.messages:
                yield "Send me a message and I'll help."
                return
            user_message = request.messages[-1].content

            # ---- Stage 2 first: the goal is read in the caller's context ---
            context = await self._context_builder.build(request, self._auth_user, request_id)
            log.log_context(context)

            # ---- Stage 1: Goal -----------------------------------------
            goal = await self._goal_builder.build(user_message, context)
            log.log_goal(goal)

            # ---- Stage 3: Input Guardrails -----------------------------
            input_guard = await self._input_guardrails.check(user_message, context, goal)
            log.log_guardrail("input", input_guard)
            if input_guard.blocked:
                response = input_guard.reason
                yield response
                return

            # ---- Stage 4: Intent ----------------------------------------
            intent = await self._intent_detector.detect(user_message, goal, context)
            log.log_intent(intent)

            # ---- Ownership + Stage 5: Planner ---------------------------
            ownership = self._ownership.resolve(goal, context)
            plan = await self._planner.plan(goal, intent, ownership, context, self._tools)
            log.log_plan(plan)

            # ---- Stages 6-8: validate, select, execute -------------------
            if plan.executes_tools:
                permission, tool_results = await self._run_tools(plan, context, log)

                if permission is not None and permission.denied:
                    plan.action = PlanAction.REJECT
                    plan.rejection_reason = permission.user_message

                elif tool_results and tool_results[-1].failed:
                    # Report the failure honestly rather than pretending.
                    async for chunk in self._generate(
                        build_tool_failure_chain(
                            request, context, self._tools, plan,
                            tool_results[-1].error or "The action did not complete.",
                            goal,
                        ),
                        log,
                    ):
                        response += chunk
                        yield chunk
                    if not response:
                        response = tool_results[-1].error or "That didn't go through."
                        fallback_used = True
                        yield response
                    return

                else:
                    for result in tool_results:
                        if result.ui_action:
                            yield _marker(ACTION_MARKER, {
                                "type": "action", "action": result.ui_action,
                            })

            # ---- Stages 9-10: reason, guard, deliver ---------------------
            async for chunk, guard in self._respond(request, context, goal, plan, tool_results, log):
                if guard is not None:
                    output_guard = guard
                    if guard.blocked:
                        response = guard.safe_replacement or ""
                        yield _marker(REPLACE_MARKER, {
                            "type": "replace", "content": response,
                        })
                        return
                    continue
                response += chunk
                yield chunk

            if not response.strip() and plan.action is PlanAction.RESPOND:
                fallback_used = True
                response = _offline_fallback(goal)
                yield response

        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            fallback_used = True
            log.log_error("pipeline", exc)
            logger.exception("Vertex pipeline failed [%s]", request_id)
            message = (
                "\n\n⚠️ Something went wrong on my side while handling that. "
                "Please try again in a moment."
            )
            response += message
            yield message

        finally:
            timings = log.log_total(goal, intent, plan)
            # Stage 11 — never allowed to affect what the user just saw.
            await self._evaluate(
                request_id=request_id,
                context=context,
                user_message=user_message,
                goal=goal,
                intent=intent,
                plan=plan,
                response=response,
                timings=timings,
                input_guard=input_guard,
                output_guard=output_guard,
                permission=permission,
                tool_results=tool_results,
                fallback_used=fallback_used,
                error=error,
                log=log,
            )

    # ------------------------------------------------------------------
    # Stages 6-8
    # ------------------------------------------------------------------

    async def _run_tools(
        self, plan: ExecutionPlan, context: VertexContext, log: PipelineLogger
    ) -> tuple[Optional[PermissionDecision], List[ToolResult]]:
        """Validate then execute each step, stopping at the first problem."""
        exec_context = ToolExecutionContext(
            vertex=context,
            db=self._db,
            auth_user=self._auth_user,
            request_id=context.request_id,
        )
        results: List[ToolResult] = []
        decision: Optional[PermissionDecision] = None

        for step in plan.steps:
            label = f"{step.tool_name}.{step.tool_action}"

            decision = self._permissions.validate(
                step, plan.ownership, context, self._tools
            )
            log.log_permission(decision, label)
            if decision.denied:
                return decision, results

            tool = self._tools.get(step.tool_name)
            if tool is None:
                results.append(
                    ToolResult(success=False, error="That capability isn't available.")
                )
                return decision, results

            try:
                result = await tool.execute(step.tool_action, step.tool_params, exec_context)
            except Exception as exc:
                # A tool contract violation, not a business failure.
                log.log_error(f"tool:{label}", exc)
                logger.exception("Tool %s raised", label)
                result = ToolResult(
                    success=False,
                    error="That action hit an unexpected problem and didn't complete.",
                )

            log.log_tool_execution(step.tool_name, step.tool_action, result)
            results.append(result)

            if result.failed:
                break

        return decision, results

    # ------------------------------------------------------------------
    # Stages 9-10
    # ------------------------------------------------------------------

    async def _respond(
        self,
        request: VertexRequest,
        context: VertexContext,
        goal: Goal,
        plan: ExecutionPlan,
        tool_results: List[ToolResult],
        log: PipelineLogger,
    ):
        """Yield ``(chunk, None)`` for text and ``(None, guard)`` for verdicts."""
        # Terminal branches carry their own copy — no model needed, and no
        # opportunity for one to soften a refusal into a suggestion.
        if plan.action is PlanAction.CLARIFY:
            text = plan.clarification_message or "Could you tell me a bit more?"
            yield text, None
            yield None, await self._guard(text, context)
            return

        if plan.action is PlanAction.REJECT:
            text = plan.rejection_reason or "I can't do that."
            yield text, None
            yield None, await self._guard(text, context)
            return

        succeeded = [r for r in tool_results if r.success]
        erp_data = {k: v for r in succeeded if r.is_erp_data for k, v in r.data.items()}

        # Ground the output guardrail in what the tools actually returned.
        self._output_guardrails.ground(erp_data, tool_produced_data=bool(erp_data))

        if plan.executes_tools and succeeded:
            answering = goal.type is GoalType.QUESTION or any(
                r.is_erp_data for r in succeeded
            )
            chain = (
                build_data_answer_chain(request, context, self._tools, succeeded, goal)
                if answering
                else build_tool_confirmation_chain(
                    request, context, self._tools, plan, succeeded, goal
                )
            )
        else:
            chain = build_prompt_chain(request, context, self._tools, goal)

        async for item in self._stream_guarded(chain, context, log, tool_results):
            yield item

    async def _stream_guarded(
        self,
        chain,
        context: VertexContext,
        log: PipelineLogger,
        tool_results: List[ToolResult],
    ):
        """Stream tokens, holding back a tail the guardrail can still veto."""
        buffer = ""
        released = 0
        streamed_anything = False

        try:
            async for token in self._provider.stream(chain):
                buffer += token
                streamed_anything = True

                safe_upto = max(len(buffer) - _GUARD_WINDOW, 0)
                if safe_upto > released:
                    verdict = await self._output_guardrails.check(buffer, context)
                    if verdict.blocked:
                        log.log_guardrail("output", verdict)
                        yield None, verdict
                        return
                    yield buffer[released:safe_upto], None
                    released = safe_upto

        except Exception as exc:
            log.log_error("llm", exc)
            logger.warning("LLM streaming failed: %s", exc)
            if not streamed_anything:
                # Tool work already succeeded; report it without the model
                # rather than losing a completed action to a provider outage.
                text = _tool_only_summary(tool_results)
                if text:
                    yield text, None
                    yield None, await self._guard(text, context)
                    return
                raise

        final = await self._output_guardrails.check(buffer, context)
        log.log_guardrail("output", final)
        if final.blocked:
            yield None, final
            return

        if len(buffer) > released:
            yield buffer[released:], None

        log.log_llm_call(
            self._provider.__class__.__name__,
            getattr(self._provider, "_model", "unknown"),
            len(buffer),
        )
        yield None, final

    async def _guard(self, text: str, context: VertexContext) -> GuardrailResult:
        return await self._output_guardrails.check(text, context)

    # ------------------------------------------------------------------
    # Stage 11
    # ------------------------------------------------------------------

    async def _evaluate(self, *, request_id, context, user_message, goal, intent,
                        plan, response, timings, input_guard, output_guard,
                        permission, tool_results, fallback_used, error, log) -> None:
        """Score and store. Swallows its own failures on purpose."""
        try:
            if context is None or goal is None or intent is None or plan is None:
                # Failed before the pipeline was assembled — nothing meaningful
                # to score, and the error is already logged.
                return

            report = await self._evaluator.evaluate(
                EvaluationInput(
                    request_id=request_id,
                    context=context,
                    user_message=user_message,
                    goal=goal,
                    intent=intent,
                    plan=plan,
                    response=response,
                    timings=timings or StageTimings(),
                    input_guardrail=input_guard,
                    output_guardrail=output_guard,
                    permission=permission,
                    tool_results=tool_results,
                    fallback_used=fallback_used,
                    error=error,
                )
            )
            log.log_evaluation(report)
            await evaluation_store.record(report, self._db)

        except Exception as exc:
            logger.warning(
                "Evaluation stage failed for request %s: %s: %s",
                request_id, type(exc).__name__, exc,
            )


# --------------------------------------------------------------------------


def _marker(marker: str, payload: dict) -> str:
    return f"{marker}{json.dumps(payload)}{marker}"


def _safe_provider() -> Optional[AIProvider]:
    try:
        return get_provider()
    except Exception as exc:
        logger.error("No LLM provider available: %s", exc)
        return _NullProvider()


def _tool_only_summary(results: List[ToolResult]) -> str:
    """Plain confirmation assembled without a model."""
    messages = [r.message for r in results if r.success and r.message]
    return f"✅ {' '.join(messages)}" if messages else ""


def _offline_fallback(goal: Optional[Goal]) -> str:
    if goal and goal.type is GoalType.QUESTION:
        return (
            "I can't reach my language model right now, so I don't want to guess "
            "at an answer. Please try again shortly."
        )
    return (
        "I'm having trouble responding right now. Please try again in a moment."
    )


class _NullProvider(AIProvider):
    """Stands in when no provider is configured.

    Raising here rather than at construction keeps every non-model stage —
    guardrails, permissions, tools — working when the key is missing, so a
    "change my theme" request still succeeds.
    """

    async def stream(self, messages, **kwargs):
        raise RuntimeError("No LLM provider is configured.")
        yield ""  # pragma: no cover — makes this an async generator

    async def complete(self, messages, **kwargs) -> str:
        raise RuntimeError("No LLM provider is configured.")
