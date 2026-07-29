"""Strategy Resolver and Registry for Roll Number operations."""
from __future__ import annotations

from typing import Dict, List, Optional, Type

from app.core.exceptions import ValidationError
from app.services.roll_number.strategies.autonomous import VVITAutonomousStrategy
from app.services.roll_number.strategies.base import RollNumberStrategy
from app.services.roll_number.strategies.university import VVITUniversityStrategy


class StrategyResolver:
    """Registry and resolver for roll number strategies."""

    def __init__(self) -> None:
        self._strategies: List[RollNumberStrategy] = []
        self._name_map: Dict[str, RollNumberStrategy] = {}

    def register_strategy(self, strategy: RollNumberStrategy) -> None:
        """Register a new strategy instance."""
        self._strategies.append(strategy)
        self._name_map[strategy.name.lower()] = strategy

    def resolve(
        self,
        roll_number: str,
        institution_code: Optional[str] = None,
        strategy_name: Optional[str] = None,
    ) -> RollNumberStrategy:
        """Resolve the appropriate strategy for a given roll number.
        
        Order of resolution:
        1. Explicit strategy_name if provided.
        2. Explicit institution_code mapping if provided.
        3. Dynamic pattern matching across registered strategies.
        """
        if strategy_name:
            strat = self._name_map.get(strategy_name.lower())
            if strat:
                return strat

        if institution_code:
            inst = institution_code.upper()
            if inst in ("AUTONOMOUS", "VVIT_AUTONOMOUS"):
                return self._name_map["vvit_autonomous"]
            if inst in ("UNIVERSITY", "VVIT_UNIVERSITY"):
                return self._name_map["vvit_university"]

        for strat in self._strategies:
            if strat.matches(roll_number):
                return strat

        # Default fallback to autonomous strategy if roll matches basic VVIT shape
        # or fallback strategy
        if self._strategies:
            return self._strategies[0]

        raise ValidationError(f"No strategy available for roll number '{roll_number}'")


# Singleton default resolver pre-loaded with institution strategies
default_resolver = StrategyResolver()
default_resolver.register_strategy(VVITAutonomousStrategy())
default_resolver.register_strategy(VVITUniversityStrategy())
