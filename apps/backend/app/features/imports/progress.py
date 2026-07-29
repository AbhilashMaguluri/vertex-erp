"""Live progress for a running import.

The import itself is one database transaction, so its progress cannot be read
out of the database while it runs — an uncommitted counter is invisible to the
polling request. The counter therefore lives in the process that is doing the
work, and the poll endpoint reads it from here.

This is in-process state by design. Behind more than one worker the poll can
land on a process that is not running the import; it then falls back to the
batch's persisted status, which is why every phase transition is also written
to the row when the transaction commits. Progress is a progress bar, not a
source of truth.
"""
from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

# Ordered so the UI can render the phase list up-front and tick through it.
PHASES = (
    ("QUEUED", "Queued"),
    ("COUNSELLORS", "Creating counsellors"),
    ("STUDENTS", "Creating students"),
    ("ASSIGNMENTS", "Assigning students to counsellors"),
    ("CREDENTIALS", "Generating credentials"),
    ("FINALISING", "Committing the import"),
    ("COMPLETED", "Completed"),
    ("FAILED", "Failed"),
)
PHASE_LABELS: Dict[str, str] = dict(PHASES)

# Weight of each phase in the overall bar. Student creation dominates because
# it genuinely does — it is one account, one profile and one enrolment each.
_PHASE_WEIGHTS = {
    "QUEUED": (0, 2),
    "COUNSELLORS": (2, 12),
    "STUDENTS": (12, 78),
    "ASSIGNMENTS": (78, 90),
    "CREDENTIALS": (90, 96),
    "FINALISING": (96, 99),
    "COMPLETED": (100, 100),
    "FAILED": (100, 100),
}

# Only the most recent imports need a live bar; anything older is read from the
# database instead. Bounded so a long-lived process cannot accumulate state.
_MAX_TRACKED = 32


@dataclass
class ImportProgress:
    batch_id: str
    phase: str = "QUEUED"
    processed: int = 0
    total: int = 0
    message: Optional[str] = None
    error: Optional[str] = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def phase_label(self) -> str:
        return PHASE_LABELS.get(self.phase, self.phase.title())

    @property
    def percent(self) -> int:
        start, end = _PHASE_WEIGHTS.get(self.phase, (0, 100))
        if self.total <= 0:
            return start
        fraction = min(1.0, max(0.0, self.processed / self.total))
        return int(round(start + (end - start) * fraction))


class _ProgressRegistry:
    def __init__(self) -> None:
        # A plain lock, not an asyncio one: entries are written from the import
        # task and read from unrelated request handlers, and every operation
        # here is a few dictionary assignments.
        self._lock = threading.Lock()
        self._entries: "OrderedDict[str, ImportProgress]" = OrderedDict()

    def start(self, batch_id: str, total: int) -> ImportProgress:
        with self._lock:
            entry = ImportProgress(batch_id=batch_id, total=total)
            self._entries[batch_id] = entry
            self._entries.move_to_end(batch_id)
            while len(self._entries) > _MAX_TRACKED:
                self._entries.popitem(last=False)
            return entry

    def update(
        self,
        batch_id: str,
        *,
        phase: Optional[str] = None,
        processed: Optional[int] = None,
        total: Optional[int] = None,
        message: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        with self._lock:
            entry = self._entries.get(batch_id)
            if entry is None:
                entry = ImportProgress(batch_id=batch_id)
                self._entries[batch_id] = entry
            if phase is not None:
                entry.phase = phase
                # A new phase restarts the within-phase counter; the overall
                # bar still moves forward because the phase weight does.
                entry.processed = 0
                entry.total = 0
            if total is not None:
                entry.total = total
            if processed is not None:
                entry.processed = processed
            if message is not None:
                entry.message = message
            if error is not None:
                entry.error = error
            entry.updated_at = datetime.now(timezone.utc)

    def advance(self, batch_id: str, message: Optional[str] = None) -> None:
        with self._lock:
            entry = self._entries.get(batch_id)
            if entry is None:
                return
            entry.processed += 1
            if message is not None:
                entry.message = message
            entry.updated_at = datetime.now(timezone.utc)

    def get(self, batch_id: str) -> Optional[ImportProgress]:
        with self._lock:
            return self._entries.get(batch_id)


progress_registry = _ProgressRegistry()
