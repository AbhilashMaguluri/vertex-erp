import pytest
from app.features.students.schemas import (
    AcademicCorrectionCreate,
    AcademicCorrectionReview,
    AcademicCorrectionClarification,
    AcademicCorrectionResponse,
    AcademicCorrectionLogResponse,
)
from app.core.enums import CorrectionRequestStatus

def test_academic_correction_schemas():
    create_data = AcademicCorrectionCreate(
        section_name="Attendance",
        current_value="68%",
        proposed_value="78%",
        description="Attendance for 3 Data Structure classes on July 15 was marked absent incorrectly while present.",
    )
    assert create_data.section_name == "Attendance"
    assert create_data.current_value == "68%"
    assert create_data.proposed_value == "78%"

    review_data = AcademicCorrectionReview(
        status="NEED_MORE_INFO",
        remarks="Please upload your attendance register signature sheet for verification.",
    )
    assert review_data.status == "NEED_MORE_INFO"

    clarification_data = AcademicCorrectionClarification(
        remarks="Attached copy of attendance register signed by Prof. Sharma.",
    )
    assert clarification_data.remarks == "Attached copy of attendance register signed by Prof. Sharma."

def test_correction_request_status_enum():
    statuses = [s.value for s in CorrectionRequestStatus]
    assert "DRAFT" in statuses
    assert "SUBMITTED" in statuses
    assert "ASSIGNED" in statuses
    assert "UNDER_REVIEW" in statuses
    assert "NEED_MORE_INFO" in statuses
    assert "APPROVED" in statuses
    assert "REJECTED" in statuses
