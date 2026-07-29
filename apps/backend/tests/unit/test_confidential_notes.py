"""Confidential counselling notes must never reach a student.

CounsellingService._to_response is the single chokepoint every session
response passes through, so testing it directly covers every endpoint that
serves a session (list, get-by-id, my-sessions, acknowledge, create) without
needing a database.
"""
from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.features.counselling.service import CounsellingService, _is_student


def _role(name):
    return SimpleNamespace(name=name)


def _user(*role_names):
    return SimpleNamespace(id="11111111-1111-1111-1111-111111111111", roles=[_role(r) for r in role_names])


def _session():
    return SimpleNamespace(
        id="22222222-2222-2222-2222-222222222222",
        student_id="33333333-3333-3333-3333-333333333333",
        counsellor_id="44444444-4444-4444-4444-444444444444",
        session_date=date(2026, 7, 26),
        session_type="ACADEMIC",
        mode="IN_PERSON",
        observations="x" * 60,
        recommendations="Attend remedial classes.",
        student_commitments="Will attend all labs.",
        confidential_notes="Family situation disclosed in confidence.",
        follow_up_required=False,
        follow_up_date=None,
        student_acknowledged=False,
        acknowledged_at=None,
        risk_assessment="MEDIUM",
        confidential=False,
        action_items=[],
        created_at=datetime.now(timezone.utc),
    )


def test_student_never_receives_confidential_notes():
    response = CounsellingService._to_response(_session(), _user("STUDENT"))
    assert response.confidential_notes is None
    # The rest of the record still reaches them — only the notes are withheld.
    assert response.recommendations == "Attend remedial classes."
    assert response.student_commitments == "Will attend all labs."
    assert response.observations == "x" * 60


def test_counsellor_receives_confidential_notes():
    response = CounsellingService._to_response(_session(), _user("COUNSELLOR"))
    assert response.confidential_notes == "Family situation disclosed in confidence."


def test_admin_receives_confidential_notes():
    response = CounsellingService._to_response(_session(), _user("ADMIN"))
    assert response.confidential_notes == "Family situation disclosed in confidence."


def test_student_with_a_second_role_is_still_treated_as_a_student():
    """A student who is also, say, a lab assistant must not gain access to
    their own confidential notes through the second role."""
    response = CounsellingService._to_response(_session(), _user("STUDENT", "FACULTY"))
    assert response.confidential_notes is None


def test_no_viewer_keeps_notes_for_internal_callers():
    response = CounsellingService._to_response(_session(), None)
    assert response.confidential_notes == "Family situation disclosed in confidence."


def test_is_student_helper():
    assert _is_student(_user("STUDENT")) is True
    assert _is_student(_user("COUNSELLOR")) is False
    assert _is_student(None) is False
