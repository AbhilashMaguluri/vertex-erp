"""Prompt chain builder.

Assembles the final message list sent to the LLM:

    System Prompt  →  Role Prompt  →  Page Prompt  →  Conversation History  →  Current Message

The result is a flat ``list[ChatMessage]`` ready for the provider.
"""

from __future__ import annotations

from typing import List

from app.ai.models.context import VertexContext
from app.ai.models.message import ChatMessage, MessageRole
from app.ai.models.request import VertexRequest
from app.ai.prompts.pages import get_page_prompt
from app.ai.prompts.roles import get_role_prompt
from app.ai.prompts.system import SYSTEM_PROMPT


def build_prompt_chain(request: VertexRequest) -> List[ChatMessage]:
    """Build the full prompt chain for the given request.

    Returns a list of ``ChatMessage`` objects with the system context
    prepended to the conversation history.
    """
    ctx: VertexContext = request.context
    chain: List[ChatMessage] = []

    # 1. Base system prompt — always first
    chain.append(
        ChatMessage(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT)
    )

    # 2. Role prompt — adds mode-specific constraints
    role_prompt = get_role_prompt(ctx.mode)
    if role_prompt:
        chain.append(
            ChatMessage(role=MessageRole.SYSTEM, content=role_prompt)
        )

    # 3. Page prompt — adds page-awareness context
    page_prompt = get_page_prompt(ctx.page)
    if page_prompt:
        chain.append(
            ChatMessage(role=MessageRole.SYSTEM, content=page_prompt)
        )

    # 4. User context injection (if authenticated)
    if ctx.user.name:
        user_line = f"The current user is **{ctx.user.name}**"
        if ctx.user.role:
            user_line += f" (role: {ctx.user.role})"
        if ctx.user.department:
            user_line += f" in the {ctx.user.department} department"
        user_line += "."
        chain.append(
            ChatMessage(role=MessageRole.SYSTEM, content=user_line)
        )

    # 5. Conversation history + current message (from the request)
    chain.extend(request.messages)

    return chain
