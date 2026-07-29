"""Base abstract class for Roll Number Strategies."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class RollMetadata:
    """Academic metadata extracted from a roll number."""

    batch_year: Optional[int] = None
    branch_code: Optional[str] = None
    branch_hint: Optional[str] = None
    college_code: Optional[str] = None
    program_code: Optional[str] = None
    is_lateral_entry: bool = False
    institution_type: Optional[str] = None


@dataclass
class RollParts:
    """Decomposed structural parts of a roll number."""

    raw: str
    cleaned: str
    academic_prefix: str  # e.g., "23BQ1A"
    batch_year_prefix: str  # e.g., "23"
    college_code: str  # e.g., "BQ"
    program_code: str  # e.g., "1A" or "5A"
    branch_code: str  # e.g., "54"
    serial_tail: str  # e.g., "01", "99", "A0", "5408"
    full_serial: str  # e.g., "5401", "54A0", "5408"
    strategy_name: str


class RollNumberStrategy(ABC):
    """Abstract Base Class for roll number parsing, validation, and range generation."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the strategy."""
        pass

    @abstractmethod
    def matches(self, roll_number: str) -> bool:
        """Check whether the given roll number string matches this strategy's pattern."""
        pass

    @abstractmethod
    def parse(self, roll_number: str) -> Optional[RollParts]:
        """Decompose a roll number string into structured RollParts."""
        pass

    @abstractmethod
    def generate_range(
        self,
        start_roll: str,
        raw_end: str,
        max_count: int = 500,
    ) -> List[str]:
        """Generate a consecutive list of roll numbers from start_roll to raw_end.
        
        Raises ValidationError if the range is invalid, backwards, or exceeds max_count.
        """
        pass

    @abstractmethod
    def validate_endpoints(
        self,
        start_parts: RollParts,
        end_parts: RollParts,
        allow_cross_batch: bool = False,
        allow_cross_dept: bool = False,
    ) -> None:
        """Validate that start and end range endpoints belong to compatible academic series."""
        pass

    @abstractmethod
    def describe(self, roll_number: str) -> RollMetadata:
        """Extract academic metadata from the roll number."""
        pass
