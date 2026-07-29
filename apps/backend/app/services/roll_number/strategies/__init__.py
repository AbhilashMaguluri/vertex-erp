"""Roll Number Strategies package."""
from app.services.roll_number.strategies.autonomous import VVITAutonomousStrategy
from app.services.roll_number.strategies.base import (
    RollMetadata,
    RollNumberStrategy,
    RollParts,
)
from app.services.roll_number.strategies.university import VVITUniversityStrategy

__all__ = [
    "RollNumberStrategy",
    "RollMetadata",
    "RollParts",
    "VVITAutonomousStrategy",
    "VVITUniversityStrategy",
]
