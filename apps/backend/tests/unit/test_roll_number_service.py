"""Unit tests for the Roll Number Service and Strategies."""
import pytest
from app.core.exceptions import ValidationError
from app.services.roll_number import (
    MAX_ROLLS_PER_RANGE,
    VVITAutonomousStrategy,
    VVITUniversityStrategy,
    describe_roll,
    expand_roll_cell,
    generate_roll_number_range,
    parse_roll,
    validate_range_endpoints,
    validate_single_roll,
)


# --------------------------------------------------------------------------
# VVIT Autonomous Strategy Range Generation
# --------------------------------------------------------------------------

def test_autonomous_transition_5499_to_54a0():
    result = generate_roll_number_range("23BQ1A5499", "54A0")
    assert result == ["23BQ1A5499", "23BQ1A54A0"]


def test_autonomous_transition_54a9_to_54b0():
    result = generate_roll_number_range("23BQ1A54A9", "54B0")
    assert result == ["23BQ1A54A9", "23BQ1A54B0"]


def test_autonomous_transition_54f9_to_54g0():
    result = generate_roll_number_range("23BQ1A54F9", "54G0")
    assert result == ["23BQ1A54F9", "23BQ1A54G0"]


def test_autonomous_range_5498_to_54a2():
    result = generate_roll_number_range("23BQ1A5498", "54A2")
    assert result == ["23BQ1A5498", "23BQ1A5499", "23BQ1A54A0", "23BQ1A54A1", "23BQ1A54A2"]


def test_autonomous_range_54a8_to_54b6():
    result = generate_roll_number_range("23BQ1A54A8", "54B6")
    expected = [
        "23BQ1A54A8", "23BQ1A54A9", "23BQ1A54B0", "23BQ1A54B1",
        "23BQ1A54B2", "23BQ1A54B3", "23BQ1A54B4", "23BQ1A54B5", "23BQ1A54B6"
    ]
    assert result == expected


def test_autonomous_range_54b9_to_54c2():
    result = generate_roll_number_range("23BQ1A54B9", "54C2")
    assert result == ["23BQ1A54B9", "23BQ1A54C0", "23BQ1A54C1", "23BQ1A54C2"]


def test_autonomous_range_54f9_to_54g4():
    result = generate_roll_number_range("23BQ1A54F9", "54G4")
    assert result == ["23BQ1A54F9", "23BQ1A54G0", "23BQ1A54G1", "23BQ1A54G2", "23BQ1A54G3", "23BQ1A54G4"]


@pytest.mark.parametrize(
    "start,end,expected_count,expected_first,expected_last",
    [
        ("23BQ1A5499", "23BQ1A54A7", 9, "23BQ1A5499", "23BQ1A54A7"),
        ("23BQ1A54A8", "23BQ1A54B6", 9, "23BQ1A54A8", "23BQ1A54B6"),
        ("23BQ1A54B7", "23BQ1A54C5", 9, "23BQ1A54B7", "23BQ1A54C5"),
        ("23BQ1A54C6", "23BQ1A54D4", 9, "23BQ1A54C6", "23BQ1A54D4"),
        ("23BQ1A54D5", "23BQ1A54E3", 9, "23BQ1A54D5", "23BQ1A54E3"),
        ("23BQ1A54E4", "23BQ1A54F2", 9, "23BQ1A54E4", "23BQ1A54F2"),
        ("23BQ1A54F3", "23BQ1A54G1", 9, "23BQ1A54F3", "23BQ1A54G1"),
    ],
)
def test_autonomous_problem_ranges_expand_correctly(start, end, expected_count, expected_first, expected_last):
    result = expand_roll_cell(f"{start} → {end}")
    assert result.ok, result.errors
    assert len(result.roll_numbers) == expected_count
    assert result.roll_numbers[0] == expected_first
    assert result.roll_numbers[-1] == expected_last


# --------------------------------------------------------------------------
# VVIT University Strategy Range Generation
# --------------------------------------------------------------------------

def test_university_decimal_range_generation():
    result = generate_roll_number_range("24BQ5A5408", "24BQ5A5412")
    assert result == [
        "24BQ5A5408", "24BQ5A5409", "24BQ5A5410", "24BQ5A5411", "24BQ5A5412"
    ]


def test_university_range_does_not_use_autonomous_progression():
    strat = VVITUniversityStrategy()
    result = strat.generate_range("24BQ5A5498", "24BQ5A5502")
    assert result == [
        "24BQ5A5498", "24BQ5A5499", "24BQ5A5500", "24BQ5A5501", "24BQ5A5502"
    ]


# --------------------------------------------------------------------------
# Strategy Auto-detection & Parsing
# --------------------------------------------------------------------------

def test_auto_detection_autonomous_vs_university():
    parts_auto = parse_roll("23BQ1A5471")
    assert parts_auto is not None
    assert parts_auto.strategy_name == "vvit_autonomous"

    parts_univ = parse_roll("24BQ5A5408")
    assert parts_univ is not None
    assert parts_univ.strategy_name in ("vvit_autonomous", "vvit_university")


def test_metadata_extraction():
    meta = describe_roll("23BQ1A5401")
    assert meta.batch_year == 2023
    assert meta.branch_code == "54"
    assert meta.branch_hint == "AI&DS"
    assert meta.college_code == "BQ"
    assert meta.is_lateral_entry is False

    meta_lat = describe_roll("24BQ5A5410")
    assert meta_lat.batch_year == 2024
    assert meta_lat.is_lateral_entry is True


# --------------------------------------------------------------------------
# Validation Rules & Erroneous Input
# --------------------------------------------------------------------------

def test_reject_backwards_range():
    with pytest.raises(ValidationError) as excinfo:
        generate_roll_number_range("23BQ1A5410", "23BQ1A5401")
    assert "ends" in str(excinfo.value) and "before it starts" in str(excinfo.value)


def test_reject_cross_batch_range():
    with pytest.raises(ValidationError) as excinfo:
        generate_roll_number_range("23BQ1A5471", "24BQ5A5471")
    assert "different series" in str(excinfo.value) or "mismatch" in str(excinfo.value)


def test_reject_cross_department_range():
    with pytest.raises(ValidationError) as excinfo:
        generate_roll_number_range("23BQ1A5401", "23BQ1A0580")
    assert any(msg in str(excinfo.value) for msg in ("Department mismatch", "different series", "before it starts", "ends"))


def test_reject_malformed_roll_number():
    with pytest.raises(ValidationError):
        validate_single_roll("INVALID_ROLL_123")


def test_max_range_limit_enforced():
    with pytest.raises(ValidationError) as excinfo:
        generate_roll_number_range("23BQ1A5401", "23BQ1A5999")
    assert "per-range limit" in str(excinfo.value) or "above the" in str(excinfo.value)


# --------------------------------------------------------------------------
# Normalization & Edge Cases
# --------------------------------------------------------------------------

def test_lowercase_and_whitespace_normalization():
    result = expand_roll_cell("  23bq1a5498   to   23bq1a54a2  ")
    assert result.ok
    assert result.roll_numbers == [
        "23BQ1A5498", "23BQ1A5499", "23BQ1A54A0", "23BQ1A54A1", "23BQ1A54A2"
    ]


def test_single_roll_expansion():
    result = expand_roll_cell("23BQ1A5471")
    assert result.ok
    assert result.roll_numbers == ["23BQ1A5471"]
