"""Abstract LLM provider interface.

Every concrete provider (Groq, Gemini, OpenAI, Ollama …) implements this
contract.  The rest of the Vertex stack never imports a concrete provider
directly — it calls ``get_provider()`` which reads the config and returns the
correct implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List

from app.ai.models.message import ChatMessage


class AIProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def stream(
        self, messages: List[ChatMessage], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Yield response tokens one at a time."""
        ...  # pragma: no cover

    @abstractmethod
    async def complete(self, messages: List[ChatMessage], **kwargs) -> str:
        """Return the full response in one shot (non-streaming fallback)."""
        ...  # pragma: no cover


def get_provider() -> AIProvider:
    """Factory that reads ``LLM_PROVIDER`` from settings and returns the
    matching concrete implementation.  Adding a new provider is a one-file
    change: implement the class, add an ``elif`` here."""

    from app.config import settings

    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "groq":
        from app.ai.providers.groq import GroqProvider

        return GroqProvider()

    # Future:
    # elif provider_name == "gemini":  ...
    # elif provider_name == "openai":  ...
    # elif provider_name == "ollama":  ...
    # elif provider_name == "qwen":    ...
    # elif provider_name == "kimi":    ...

    raise ValueError(
        f"Unknown LLM_PROVIDER '{settings.LLM_PROVIDER}'. "
        "Supported: groq.  Set LLM_PROVIDER in .env."
    )
