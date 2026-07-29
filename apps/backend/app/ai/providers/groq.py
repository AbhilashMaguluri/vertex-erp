"""Groq LLM provider — the *only* file that imports or references the Groq SDK.

Swap to a different provider by changing ``LLM_PROVIDER`` in ``.env`` and
implementing a new ``AIProvider`` subclass.  No other file needs to change.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator, List

from app.ai.models.message import ChatMessage
from app.ai.providers.base import AIProvider

logger = logging.getLogger(__name__)


class GroqProvider(AIProvider):
    """Concrete provider backed by the Groq inference API."""

    def __init__(self) -> None:
        from app.config import settings

        self._api_key: str = settings.GROQ_API_KEY
        self._model: str = settings.LLM_MODEL

    # ------------------------------------------------------------------
    # AIProvider interface
    # ------------------------------------------------------------------

    async def stream(
        self, messages: List[ChatMessage], **kwargs
    ) -> AsyncGenerator[str, None]:
        client = self._get_client()
        formatted = self._format_messages(messages)

        stream = await client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=formatted,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2048),
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def complete(self, messages: List[ChatMessage], **kwargs) -> str:
        client = self._get_client()
        formatted = self._format_messages(messages)

        response = await client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=formatted,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2048),
            stream=False,
        )

        return response.choices[0].message.content or ""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self):
        """Lazy-import and instantiate the async Groq client."""
        if not self._api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured. "
                "Add it to apps/backend/.env to enable Vertex AI."
            )

        from groq import AsyncGroq

        return AsyncGroq(api_key=self._api_key)

    @staticmethod
    def _format_messages(messages: List[ChatMessage]) -> list[dict]:
        """Convert internal ``ChatMessage`` list to the dict format the Groq
        SDK expects (OpenAI-compatible)."""
        return [{"role": m.role.value, "content": m.content} for m in messages]
