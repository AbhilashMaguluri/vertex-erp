"""Roll Number Service package.

Single source of truth for roll number parsing, validation, metadata extraction,
and range generation across Autonomous and University institutions.
"""
from app.services.roll_number.base import StrategyResolver, default_resolver
from app.services.roll_number.generator import (
    ExpansionResult,
    expand_roll_cell,
    generate_roll_number_range,
    normalise_cell,
)
from app.services.roll_number.parser import describe_roll, parse_roll
from app.services.roll_number.strategies import (
    RollMetadata,
    RollNumberStrategy,
    RollParts,
    VVITAutonomousStrategy,
    VVITUniversityStrategy,
)
from app.services.roll_number.validators import (
    MAX_ROLLS_PER_FILE,
    MAX_ROLLS_PER_RANGE,
    validate_range_endpoints,
    validate_single_roll,
)

__all__ = [
    # Parser & Metadata
    "parse_roll",
    "describe_roll",
    # Generator
    "generate_roll_number_range",
    "expand_roll_cell",
    "normalise_cell",
    "ExpansionResult",
    # Validators & Constants
    "validate_single_roll",
    "validate_range_endpoints",
    "MAX_ROLLS_PER_RANGE",
    "MAX_ROLLS_PER_FILE",
    # Strategies & Resolver
    "StrategyResolver",
    "default_resolver",
    "RollMetadata",
    "RollParts",
    "RollNumberStrategy",
    "VVITAutonomousStrategy",
    "VVITUniversityStrategy",
]
