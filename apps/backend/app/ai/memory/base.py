"""Memory store interface and MVP no-op implementation.

In the MVP, conversation history travels with every request from the
frontend.  This interface exists so a persistent store (Redis, pgvector,
PostgreSQL) can be plugged in later without changing any upstream code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from app.ai.models.message import ChatMessage


class MemoryStore(ABC):
    """Abstract conversation memory."""

    @abstractmethod
    async def save(self, session_id: str, messages: List[ChatMessage]) -> None:
        ...  # pragma: no cover

    @abstractmethod
    async def load(self, session_id: str) -> List[ChatMessage]:
        ...  # pragma: no cover

    @abstractmethod
    async def clear(self, session_id: str) -> None:
        ...  # pragma: no cover


class InMemoryStore(MemoryStore):
    """MVP no-op — history comes from the frontend on every request."""

    async def save(self, session_id: str, messages: List[ChatMessage]) -> None:
        pass  # No-op: frontend owns history in MVP

    async def load(self, session_id: str) -> List[ChatMessage]:
        return []  # No server-side history in MVP

    async def clear(self, session_id: str) -> None:
        pass  # No-op
