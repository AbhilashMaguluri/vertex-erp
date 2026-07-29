"""Caseload scoping: who a `counsellor_id` filter is allowed to mean.

`_resolve_caseload_scope` decides whose students a caseload request returns.
Getting it wrong means an unscoped query, and an unscoped caseload query is
the entire institution's student roster — so the rules are pinned here.
"""
from types import SimpleNamespace

import pytest

from app.core.exceptions import ForbiddenError
from app.features.students.router import _resolve_caseload_scope

COUNSELLOR_ID = "11111111-1111-1111-1111-111111111111"
OTHER_ID = "99999999-9999-9999-9999-999999999999"


def _user(*role_names, user_id=COUNSELLOR_ID):
    return SimpleNamespace(id=user_id, roles=[SimpleNamespace(name=r) for r in role_names])


def test_counsellor_is_pinned_to_their_own_caseload():
    scope = _resolve_caseload_scope(_user("COUNSELLOR"), counsellor_id=None)
    assert scope == COUNSELLOR_ID


def test_counsellor_cannot_read_another_counsellors_caseload():
    """A supplied counsellor_id is discarded, not honoured — otherwise the
    filter doubles as a way to read a colleague's students."""
    scope = _resolve_caseload_scope(_user("COUNSELLOR"), counsellor_id=OTHER_ID)
    assert scope == COUNSELLOR_ID


def test_admin_may_scope_to_a_specific_counsellor():
    scope = _resolve_caseload_scope(_user("ADMIN"), counsellor_id=OTHER_ID)
    assert scope == OTHER_ID


def test_admin_without_a_filter_is_institution_wide():
    assert _resolve_caseload_scope(_user("ADMIN"), counsellor_id=None) is None


def test_hod_is_institution_wide():
    assert _resolve_caseload_scope(_user("HOD"), counsellor_id=None) is None


def test_counsellor_who_is_also_admin_is_not_scoped_down():
    """An ADMIN who also holds COUNSELLOR keeps institution-wide reach."""
    assert _resolve_caseload_scope(_user("COUNSELLOR", "ADMIN"), counsellor_id=None) is None


def test_student_is_refused_outright():
    with pytest.raises(ForbiddenError):
        _resolve_caseload_scope(_user("STUDENT"), counsellor_id=None)


def test_student_holding_a_second_role_is_still_refused():
    with pytest.raises(ForbiddenError):
        _resolve_caseload_scope(_user("STUDENT", "COUNSELLOR"), counsellor_id=None)
