"""Prompt chain builder.

Assembles what the model sees:

    System → Role → Capabilities → Page → Identity → Workspace →
    Conversation summary → History → Current message

Two things this deliberately does *not* do: it never asks the model to decide
whether to act, and it never lets the model believe it has data it was not
given. By the time this runs the plan has already executed; the model is
writing the sentence that reports it.
"""

from __future__ import annotations

import json
from typing import List, Optional

from app.ai.core.permissions import summarise_permissions
from app.ai.models.context import VertexContext
from app.ai.models.goal import Goal
from app.ai.models.message import ChatMessage, MessageRole
from app.ai.models.plan import ExecutionPlan
from app.ai.models.request import VertexRequest
from app.ai.prompts.pages import get_page_prompt
from app.ai.prompts.roles import get_role_prompt
from app.ai.prompts.system import SYSTEM_PROMPT
from app.ai.tools.base import ToolRegistry, ToolResult

#: Turns of history to replay. Older turns are covered by the rolling summary,
#: so this bounds prompt growth without losing the thread.
_HISTORY_LIMIT = 12


def build_prompt_chain(
    request: VertexRequest,
    context: Optional[VertexContext] = None,
    registry: Optional[ToolRegistry] = None,
    goal: Optional[Goal] = None,
) -> List[ChatMessage]:
    """Build the base chain for a request."""
    ctx = context or request.context
    chain: List[ChatMessage] = [
        ChatMessage(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT)
    ]

    role_prompt = get_role_prompt(ctx.mode)
    if role_prompt:
        chain.append(ChatMessage(role=MessageRole.SYSTEM, content=role_prompt))

    if registry is not None:
        chain.append(
            ChatMessage(role=MessageRole.SYSTEM, content=_capabilities_block(registry))
        )

    page_prompt = get_page_prompt(ctx.page)
    if page_prompt:
        chain.append(ChatMessage(role=MessageRole.SYSTEM, content=page_prompt))

    identity = _identity_block(ctx)
    if identity:
        chain.append(ChatMessage(role=MessageRole.SYSTEM, content=identity))

    if goal is not None:
        chain.append(
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=(
                    f"## Understood Goal\n"
                    f"The user's goal has already been analysed as: "
                    f"**{goal.statement}**. Answer that goal — do not re-interpret "
                    f"the request as something else."
                ),
            )
        )

    if ctx.conversation_summary:
        chain.append(
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=f"## Conversation So Far\n{ctx.conversation_summary}",
            )
        )

    chain.extend(request.messages[-_HISTORY_LIMIT:])
    return chain


def build_tool_confirmation_chain(
    request: VertexRequest,
    context: VertexContext,
    registry: ToolRegistry,
    plan: ExecutionPlan,
    results: List[ToolResult],
    goal: Optional[Goal] = None,
) -> List[ChatMessage]:
    """Chain for reporting work that has *already happened*.

    The instruction is emphatic about tense because the failure mode is
    specific and common: a model told about an action it did not perform tends
    to explain how the user could perform it.
    """
    chain = build_prompt_chain(request, context, registry, goal)

    executed = [
        {
            "tool": plan.tool_name,
            "action": plan.tool_action,
            "outcome": result.message,
            "data": result.data,
        }
        for result in results
        if result.success
    ]

    facts = json.dumps(executed, default=str)[:4000]

    chain.append(
        ChatMessage(
            role=MessageRole.SYSTEM,
            content=(
                "## Completed Action — Report It\n"
                "You have ALREADY performed the following on the user's behalf. "
                "It is done; it is not a suggestion and not a plan.\n\n"
                f"{facts}\n\n"
                "Write the confirmation:\n"
                "- Start with ✅ and confirm in past tense ('I've updated…', 'Opened…').\n"
                "- One or two sentences. No preamble.\n"
                "- NEVER tell the user how to do it manually — it is already done.\n"
                "- State ONLY figures that appear in the data above. If a number "
                "is not there, do not mention a number at all.\n"
                "- If the data is empty, confirm the action without inventing detail."
            ),
        )
    )
    return chain


def build_tool_failure_chain(
    request: VertexRequest,
    context: VertexContext,
    registry: ToolRegistry,
    plan: ExecutionPlan,
    error: str,
    goal: Optional[Goal] = None,
) -> List[ChatMessage]:
    """Chain for explaining a failure honestly."""
    chain = build_prompt_chain(request, context, registry, goal)
    chain.append(
        ChatMessage(
            role=MessageRole.SYSTEM,
            content=(
                "## Action Failed — Explain It\n"
                f"You attempted `{plan.tool_name}.{plan.tool_action}` and it did "
                f"not succeed. The reason:\n\n{error}\n\n"
                "Tell the user plainly, in one or two sentences, that it did not "
                "go through and why. Do not claim it worked. Do not apologise "
                "more than once. If there is an obvious next step, offer it."
            ),
        )
    )
    return chain


def build_data_answer_chain(
    request: VertexRequest,
    context: VertexContext,
    registry: ToolRegistry,
    results: List[ToolResult],
    goal: Optional[Goal] = None,
) -> List[ChatMessage]:
    """Chain for answering a question from records a tool just read.

    The retrieved data is the *only* permitted source of figures. Anything the
    model adds beyond it will be caught by the output guardrail, so the
    instruction and the enforcement agree.
    """
    chain = build_prompt_chain(request, context, registry, goal)

    payload = json.dumps(
        [{"summary": r.message, "data": r.data} for r in results if r.success],
        default=str,
    )[:6000]

    chain.append(
        ChatMessage(
            role=MessageRole.SYSTEM,
            content=(
                "## Retrieved Records — Your Only Source\n"
                f"{payload}\n\n"
                "Answer the user's question using this data and nothing else.\n"
                "- Every number you state must appear above, exactly.\n"
                "- If the answer is not in the data, say you don't have it — never estimate.\n"
                "- Format multi-row data as a compact Markdown table.\n"
                "- Be direct: lead with the answer, then any useful context."
            ),
        )
    )
    return chain


# --------------------------------------------------------------------------


def _identity_block(ctx: VertexContext) -> str:
    """Who the user is, what they may do, and what is on screen."""
    if not ctx.user.is_authenticated:
        return (
            "## Current User\n"
            "The user is **not signed in**. You have no access to any ERP record "
            "for them. Offer help with signing in when relevant."
        )

    lines = [f"## Current User\n- Name: **{ctx.user.name}**"]
    if ctx.user.role:
        lines.append(f"- Role: {ctx.user.role}")
    if ctx.user.department:
        lines.append(f"- Department: {ctx.user.department}")
    if ctx.user.roll_number:
        lines.append(f"- Roll number: {ctx.user.roll_number}")

    permissions = summarise_permissions(ctx)
    if permissions:
        lines.append(f"- Permissions: {permissions}")

    if ctx.workspace.student_id and ctx.workspace.accessible and not ctx.is_student:
        lines.append(
            f"\n### Student In View\n"
            f"The user is working on **{ctx.workspace.student_name or 'a student'}** "
            f"({ctx.workspace.student_roll or 'no roll number'}). "
            f'When they say "this student", they mean this one — never ask which.'
        )

    lines.append(
        "\nYou already know all of the above. Never ask the user to tell you "
        "who they are, what their role is, or which page they are on."
    )
    return "\n".join(lines)


def _capabilities_block(registry: ToolRegistry) -> str:
    """What Vertex can actually do, so it neither over- nor under-promises."""
    lines = [
        "## Your Capabilities",
        "These actions are wired up and are performed FOR the user, automatically:",
    ]
    for tool in registry.get_all_descriptions():
        actions = ", ".join(a["name"] for a in tool["actions"])
        lines.append(f"- **{tool['name']}** — {tool['description']} ({actions})")
    lines.append(
        "\nWhen a request matches one of these, it has already been executed "
        "before you were asked to reply. Never instruct the user to do it "
        "manually. If something is genuinely outside this list, say so plainly "
        "and point to the screen that handles it."
    )
    return "\n".join(lines)
