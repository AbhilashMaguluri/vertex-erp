"""Office Import parsing — roll ranges, sheet detection and identity generation.

Pure unit tests: no database, no app. Everything here is the logic that decides
what an office sheet *means*, which is the part that has to be right before any
account is created from it.
"""
import io

import pytest

from app.core.security import generate_readable_password
from app.features.imports import naming
from app.features.imports.parser import parse_office_file
from app.features.imports.rollnumbers import (
    MAX_ROLLS_PER_RANGE,
    describe_roll,
    expand_roll_cell,
)
from app.core.exceptions import ValidationError


# --------------------------------------------------------------------------
# Roll number ranges
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "cell",
    [
        "23BQ1A5401 to 23BQ1A5410",
        "23BQ1A5401-5410",
        "23BQ1A5401 - 23BQ1A5410",
        "23BQ1A5401 – 23BQ1A5410",     # en dash
        "23BQ1A5401 — 23BQ1A5410",     # em dash
        "23BQ1A5401 upto 5410",
        "23BQ1A5401 up to 23BQ1A5410",
        "23BQ1A5401 UPTO 10",
        "23BQ1A5401 TO 23BQ1A5410",
        "23bq1a5401 to 23bq1a5410",
        "23BQ1A5401..23BQ1A5410",
        "  23BQ1A5401   to   23BQ1A5410  ",
    ],
)
def test_every_office_range_format_expands_to_the_same_ten_students(cell):
    result = expand_roll_cell(cell)
    assert result.ok, result.errors
    assert len(result.roll_numbers) == 10
    assert result.roll_numbers[0] == "23BQ1A5401"
    assert result.roll_numbers[-1] == "23BQ1A5410"


def test_single_roll_number_is_one_student():
    result = expand_roll_cell("23BQ1A5401")
    assert result.roll_numbers == ["23BQ1A5401"]


def test_lists_and_ranges_mix_in_one_cell():
    result = expand_roll_cell("23BQ1A5401 to 23BQ1A5403, 23BQ1A5461 & 23BQ1A5470")
    assert result.roll_numbers == [
        "23BQ1A5401", "23BQ1A5402", "23BQ1A5403", "23BQ1A5461", "23BQ1A5470",
    ]


def test_newline_separated_rolls_in_one_cell():
    result = expand_roll_cell("23BQ1A5401\n23BQ1A5402\n23BQ1A5403")
    assert result.roll_numbers == ["23BQ1A5401", "23BQ1A5402", "23BQ1A5403"]


def test_lateral_entry_series_keeps_its_own_prefix():
    result = expand_roll_cell("24BQ5A5401-5403")
    assert result.roll_numbers == ["24BQ5A5401", "24BQ5A5402", "24BQ5A5403"]


def test_zero_padding_is_preserved_across_a_boundary():
    result = expand_roll_cell("23BQ1A5498 to 23BQ1A5502")
    assert result.roll_numbers == [
        "23BQ1A5498", "23BQ1A5499", "23BQ1A5500", "23BQ1A5501", "23BQ1A5502",
    ]


def test_duplicate_inside_one_cell_is_collapsed_with_a_warning():
    result = expand_roll_cell("23BQ1A5401, 23BQ1A5401")
    assert result.roll_numbers == ["23BQ1A5401"]
    assert any("more than once" in w for w in result.warnings)


def test_backwards_range_is_an_error_not_an_empty_list():
    result = expand_roll_cell("23BQ1A5410 to 23BQ1A5401")
    assert not result.ok
    assert any("before it starts" in e for e in result.errors)


def test_mismatched_series_endpoints_are_rejected():
    result = expand_roll_cell("23BQ1A5401 to 24BQ1A5410")
    assert not result.ok
    assert any("different series" in e for e in result.errors)


def test_absurd_range_is_capped_rather_than_generating_thousands_of_accounts():
    result = expand_roll_cell("23BQ1A5401 to 23BQ1A9999")
    assert not result.ok
    assert result.roll_numbers == []
    assert any(str(MAX_ROLLS_PER_RANGE) in e for e in result.errors)


def test_blank_and_unreadable_cells_report_why():
    assert expand_roll_cell("").errors
    assert expand_roll_cell("   ").errors
    assert not expand_roll_cell("to be allotted").ok


# --------------------------------------------------------------------------
# What a roll number itself says
# --------------------------------------------------------------------------

def test_roll_number_reveals_batch_and_branch():
    meta = describe_roll("23BQ1A5401")
    assert meta.batch_year == 2023
    assert meta.branch_code == "54"
    assert meta.branch_hint == "AI&DS"
    assert meta.college_code == "BQ"
    assert meta.is_lateral_entry is False


def test_lateral_entry_stream_is_flagged():
    assert describe_roll("24BQ5A5410").is_lateral_entry is True


def test_off_pattern_roll_still_yields_the_admission_year():
    meta = describe_roll("21XYZ999")
    assert meta.batch_year == 2021
    assert meta.branch_hint is None


def test_unreadable_roll_claims_nothing():
    meta = describe_roll("ABCDEF")
    assert meta.batch_year is None
    assert meta.branch_code is None


# --------------------------------------------------------------------------
# Sheet parsing
# --------------------------------------------------------------------------

def _workbook(rows, sheet_title="Counsellor Allotment") -> bytes:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_title
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


OFFICE_ROWS = [
    ["VASIREDDY VENKATADRI INSTITUTE OF TECHNOLOGY"],
    ["Department of AI & DS — Counsellor Allotment 2026-27"],
    [],
    ["S.No", "Student Roll Numbers", "Counselor Name", "Counselor Mobile"],
    [1, "23BQ1A5401 to 23BQ1A5410", "Dr. S. Ravindra", "9440053880"],
    [2, "23BQ1A5411 to 23BQ1A5420", "Dr. K. Satheesh", "9949397532"],
]


def test_header_is_found_below_the_title_rows():
    parsed = parse_office_file("allotment.xlsx", _workbook(OFFICE_ROWS))
    assert parsed.header_row_number == 4
    assert parsed.sheet_name == "Counsellor Allotment"
    assert set(parsed.detected_columns) == {"roll_range", "counsellor_name", "counsellor_phone"}


def test_serial_number_column_is_ignored_entirely():
    parsed = parse_office_file("allotment.xlsx", _workbook(OFFICE_ROWS))
    assert "serial" not in parsed.detected_columns
    assert "S.No" in parsed.ignored_columns


def test_rows_expand_into_students_with_their_counsellor():
    parsed = parse_office_file("allotment.xlsx", _workbook(OFFICE_ROWS))
    assert len(parsed.rows) == 2
    first = parsed.rows[0]
    assert len(first.roll_numbers) == 10
    assert first.counsellor_name == "Dr. S. Ravindra"
    assert first.counsellor_phone == "9440053880"
    assert first.row_number == 5


def test_csv_is_read_the_same_way_as_excel():
    csv_bytes = (
        "S.No,Student Roll Numbers,Counselor Name,Counselor Mobile\n"
        "1,23BQ1A5401 to 23BQ1A5405,Dr. S. Ravindra,9440053880\n"
    ).encode("utf-8")
    parsed = parse_office_file("allotment.csv", csv_bytes)
    assert len(parsed.rows) == 1
    assert len(parsed.rows[0].roll_numbers) == 5
    assert parsed.rows[0].counsellor_name == "Dr. S. Ravindra"


def test_alternative_column_wordings_are_recognised():
    parsed = parse_office_file(
        "allotment.xlsx",
        _workbook([
            ["Roll Nos", "Name of the Counsellor", "Mobile", "Section", "Branch"],
            ["23BQ1A5401-5402", "Prof. Lakshmi Prasanna", "9848012345", "A", "AI&DS"],
        ]),
    )
    assert set(parsed.detected_columns) >= {"roll_range", "counsellor_name", "section", "department"}
    row = parsed.rows[0]
    # A bare "Mobile" next to a counsellor column belongs to the counsellor.
    assert row.counsellor_phone == "9848012345"
    assert row.section == "A"
    assert row.department == "AI&DS"


def test_blank_spacer_rows_are_skipped_not_reported_as_errors():
    parsed = parse_office_file(
        "allotment.xlsx",
        _workbook([
            ["Student Roll Numbers", "Counselor Name"],
            ["23BQ1A5401", "Dr. S. Ravindra"],
            [None, None],
            ["", ""],
            ["23BQ1A5402", "Dr. K. Satheesh"],
        ]),
    )
    assert len(parsed.rows) == 2


def test_a_file_without_a_roll_column_is_refused_with_a_useful_message():
    with pytest.raises(ValidationError) as excinfo:
        parse_office_file("wrong.xlsx", _workbook([["Name", "Designation"], ["Ravindra", "Professor"]]))
    assert "roll-number column" in str(excinfo.value)


def test_unsupported_file_type_is_refused():
    with pytest.raises(ValidationError):
        parse_office_file("notes.txt", b"whatever")


def test_short_phone_values_are_dropped_rather_than_stored():
    parsed = parse_office_file(
        "allotment.xlsx",
        _workbook([
            ["Student Roll Numbers", "Counselor Name", "Counselor Mobile"],
            ["23BQ1A5401", "Dr. S. Ravindra", "N/A"],
        ]),
    )
    assert parsed.rows[0].counsellor_phone is None


# --------------------------------------------------------------------------
# Identity generation
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "written,first,last",
    [
        ("Dr. S. Ravindra", "Ravindra", "S"),
        ("Dr. K. Satheesh", "Satheesh", "K"),
        ("Prof. Lakshmi Prasanna", "Lakshmi", "Prasanna"),
        ("Ravindra S.", "Ravindra", "S"),
        ("Smt. G. Naga Lakshmi", "Naga Lakshmi", "G"),
    ],
)
def test_office_written_names_split_the_way_the_convention_reads(written, first, last):
    person = naming.split_person_name(written)
    assert person.first_name == first
    assert person.last_name == last


def test_the_same_person_spelled_three_ways_shares_one_key():
    keys = {
        naming.normalise_person_key("Dr. S. Ravindra"),
        naming.normalise_person_key("S Ravindra"),
        naming.normalise_person_key("Ravindra S."),
        naming.normalise_person_key("  RAVINDRA   S  "),
    }
    assert len(keys) == 1


def test_different_people_do_not_collide():
    assert naming.normalise_person_key("Dr. S. Ravindra") != naming.normalise_person_key("Dr. K. Satheesh")


def test_preferred_username_is_firstname_dot_initial():
    person = naming.split_person_name("Dr. S. Ravindra")
    assert naming.counsellor_username_candidates(person)[0] == "ravindra.s"
    assert "dr.s.ravindra" in naming.counsellor_username_candidates(person)


def test_username_collisions_fall_through_to_the_next_form():
    person = naming.split_person_name("Dr. S. Ravindra")
    username, email = naming.allocate_counsellor_identity(
        person, "vvit.net", {"ravindra.s"}, {"ravindra.s@vvit.net"}
    )
    assert username != "ravindra.s"
    assert email == f"{username}@vvit.net"


def test_username_collisions_eventually_suffix_a_number():
    person = naming.split_person_name("Dr. S. Ravindra")
    taken_usernames = set(naming.counsellor_username_candidates(person))
    taken_emails = {f"{u}@vvit.net" for u in taken_usernames}
    username, _ = naming.allocate_counsellor_identity(person, "vvit.net", taken_usernames, taken_emails)
    assert username not in taken_usernames
    assert username.endswith("2")


def test_a_students_username_is_their_roll_number():
    assert naming.student_username("23bq1a5401") == "23BQ1A5401"
    assert naming.student_email("23BQ1A5401", "vvit.net") == "23bq1a5401@vvit.net"


# --------------------------------------------------------------------------
# Issued passwords
# --------------------------------------------------------------------------

def test_readable_password_has_every_character_class_and_no_look_alikes():
    for _ in range(200):
        password = generate_readable_password()
        assert len(password) == 8
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in "@#$%&*+?" for c in password)
        assert not set(password) & set("0O1lI")


def test_readable_passwords_are_not_repeated():
    assert len({generate_readable_password() for _ in range(200)}) > 190


def test_a_password_too_short_to_hold_every_class_is_refused():
    with pytest.raises(ValueError):
        generate_readable_password(3)
