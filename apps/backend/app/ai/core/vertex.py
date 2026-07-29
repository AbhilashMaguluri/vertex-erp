"""Vertex Core — the central orchestrator with the full agent pipeline.

Pipeline:
    User Message
    → Input Guardrails
    → Intent Detection
    → Planner
    → Tool Execution (if required)
    → LLM Response Generation
    → Output Guardrails
    → Response

Each stage is independently replaceable.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import AsyncGenerator

from app.ai.core.guardrails import InputGuardrails, OutputGuardrails
from app.ai.core.intent import IntentDetector
from app.ai.core.logging import PipelineLogger
from app.ai.core.planner import Planner
from app.ai.memory.base import InMemoryStore, MemoryStore
from app.ai.models.message import ChatMessage, MessageRole
from app.ai.models.plan import PlanAction
from app.ai.models.request import VertexRequest
from app.ai.prompts.builder import build_prompt_chain
from app.ai.providers.base import AIProvider, get_provider
from app.ai.quality.evals import QualityRunner
from app.ai.tools.base import ToolRegistry
from app.ai.tools.registry_setup import create_default_registry

logger = logging.getLogger(__name__)


class VertexCore:
    """The brain of Vertex — full agent pipeline."""

    def __init__(
        self,
        provider: AIProvider | None = None,
        memory: MemoryStore | None = None,
        tools: ToolRegistry | None = None,
        intent_detector: IntentDetector | None = None,
        planner: Planner | None = None,
        input_guardrails: InputGuardrails | None = None,
        output_guardrails: OutputGuardrails | None = None,
        quality: QualityRunner | None = None,
    ) -> None:
        self._provider = provider or get_provider()
        self._memory = memory or InMemoryStore()
        self._tools = tools or create_default_registry()
        self._intent_detector = intent_detector or IntentDetector()
        self._planner = planner or Planner()
        self._input_guardrails = input_guardrails or InputGuardrails()
        self._output_guardrails = output_guardrails or OutputGuardrails()
        self._quality = quality or QualityRunner()

    async def process(self, request: VertexRequest) -> AsyncGenerator[str, None]:
        """Process a request through the full agent pipeline."""
        request_id = str(uuid.uuid4())[:8]
        pipe_log = PipelineLogger(request_id=request_id)
        accumulated_response = ""

        try:
            # Extract user message (always the last message)
            if not request.messages:
                yield "Please send a message to get started."
                return

            user_message = request.messages[-1].content

            # ----- 1. Intent Detection -----
            intent = await self._intent_detector.detect(
                user_message, request.context
            )
            pipe_log.log_intent(intent)

            # ----- 2. Input Guardrails -----
            guard_result = await self._input_guardrails.check(
                user_message, intent, request.context
            )
            pipe_log.log_guardrail("input", guard_result)
            if not guard_result.passed:
                yield guard_result.reason
                return

            # ----- 3. Planner -----
            plan = await self._planner.plan(
                intent, request.context, self._tools
            )
            pipe_log.log_plan(plan)

            # ----- 4. Execute Plan -----

            if plan.action == PlanAction.EXECUTE_TOOL:
                # Get the tool
                tool = self._tools.get(plan.tool_name)
                if tool is None:
                    yield f"Tool '{plan.tool_name}' is not available."
                    return

                # Execute the tool
                result = await tool.execute(
                    plan.tool_action, plan.tool_params, request.context
                )
                pipe_log.log_tool_execution(
                    plan.tool_name, plan.tool_action, result
                )

                if not result.success:
                    yield result.error or "The action could not be completed."
                    return

                # Emit UI action event if the tool produced one
                if result.ui_action:
                    action_event = json.dumps({
                        "type": "action",
                        "action": result.ui_action,
                    })
                    yield f"__SSE_ACTION__{action_event}__SSE_ACTION__"

                # Stream LLM confirmation for the completed action
                confirmation_messages = self._build_tool_confirmation(
                    request, plan, result
                )
                async for token in self._provider.stream(confirmation_messages):
                    accumulated_response += token
                    yield token

                pipe_log.log_llm_call(
                    self._provider.__class__.__name__,
                    getattr(self._provider, "_model", "unknown"),
                )

            elif plan.action == PlanAction.CLARIFY:
                yield plan.clarification_message or "Could you clarify what you'd like me to do?"
                return

            elif plan.action == PlanAction.REJECT:
                yield f"⚠️ {plan.rejection_reason or 'This request cannot be processed.'}"
                return

            else:
                # PlanAction.RESPOND — direct LLM streaming (original behavior)
                messages = build_prompt_chain(request)
                async for token in self._provider.stream(messages):
                    accumulated_response += token
                    yield token

                pipe_log.log_llm_call(
                    self._provider.__class__.__name__,
                    getattr(self._provider, "_model", "unknown"),
                )

            # ----- 5. Output Guardrails -----
            if accumulated_response:
                out_guard = await self._output_guardrails.check(accumulated_response)
                pipe_log.log_guardrail("output", out_guard)

            # ----- 6. Quality Evals (async, non-blocking) -----
            if accumulated_response:
                eval_context = {
                    "mode": request.context.mode,
                    "intent_category": intent.category.value,
                    "tool_used": plan.tool_name,
                }
                await self._quality.run_all(
                    user_message, accumulated_response, eval_context
                )

            # ----- 7. Log total -----
            pipe_log.log_total(intent.category.value, plan.action.value)

        except RuntimeError as exc:
            logger.warning("Vertex processing error: %s", exc)
            yield f"\n\n⚠️ {exc}"

        except Exception as exc:
            logger.exception("Unexpected error in VertexCore.process")
            yield (
                "\n\n⚠️ I encountered an unexpected error while processing "
                "your request. Please try again in a moment."
            )

    def _build_tool_confirmation(
        self, request: VertexRequest, plan, result
    ) -> list[ChatMessage]:
        """Build a prompt chain that tells the LLM to confirm a completed action."""
        # Start with the system prompt chain for context
        messages = build_prompt_chain(request)

        # Add a system instruction telling the LLM to confirm the action
        messages.append(
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=(
                    f"You have just successfully executed the following action:\n"
                    f"- Tool: {plan.tool_name}\n"
                    f"- Action: {plan.tool_action}\n"
                    f"- Parameters: {json.dumps(plan.tool_params)}\n"
                    f"- Result: {result.message}\n\n"
                    f"Respond with a brief, friendly confirmation message. "
                    f"Start with ✅. Be concise — one or two sentences maximum. "
                    f"Do NOT explain how to do it manually. "
                    f"The action has ALREADY been performed."
                ),
            )
        )
        return messages
