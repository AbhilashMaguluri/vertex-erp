"""Row-level access scoping beyond the coarse-grained permission model.

`require_permission`/`require_role` (app/core/permissions.py) answer "can
this ROLE perform this action at all" — they don't know which specific
student a COUNSELLOR is allowed to touch. A COUNSELLOR holds `student.read`,
`counselling.read`, etc. across the whole institution, but per the RBAC spec
counsellors may only manage students actually assigned to them. This module
adds that narrower, row-level check on top of the existing permission
dependencies.

ADMIN/SUPER_ADMIN/HOD are institution-wide by design and are never scoped
here. FACULTY caseload scoping (assigned sections) is a separate, larger
change and is intentionally out of scope for this pass.
"""
from app.core.exceptions import ForbiddenError
from app.features.auth.models import User
from app.features.students.repository import StudentRepository

_UNSCOPED_ROLES = {"ADMIN", "SUPER_ADMIN", "HOD"}


def is_assignment_scoped_counsellor(user: User) -> bool:
    role_names = {r.name for r in user.roles}
    return "COUNSELLOR" in role_names and not (role_names & _UNSCOPED_ROLES)


async def ensure_student_assigned_to_counsellor(
    user: User, student_id: str, repo: StudentRepository
) -> None:
    """403s if `user` is an assignment-scoped counsellor and `student_id` is
    not currently assigned to them. No-op for every other role — the
    permission dependency already governs whether they may act at all."""
    if not is_assignment_scoped_counsellor(user):
        return
    student = await repo.get_student_by_id(student_id)
    if not student:
        return  # let the caller's own NotFoundError handling take it from here
    assigned = any(
        a.counsellor_id == user.id and a.effective_to is None
        for a in student.counsellor_assignments
    )
    if not assigned:
        raise ForbiddenError("You may only access students assigned to you.")


async def ensure_student_record_access(
    user: User, student_id: str, repo: StudentRepository
) -> None:
    """Full row-level gate for any per-student record endpoint.

    Combines the two ownership rules that must hold on every such request:

      * a STUDENT may only ever reach their OWN student row. They hold
        attendance.read / academics.read / student.read for their own record,
        so without this check those permissions read as "any student's
        record" and the id in the URL is a straight IDOR.
      * a COUNSELLOR may only reach students currently assigned to them.

    ADMIN/SUPER_ADMIN/HOD are institution-wide and pass through.
    """
    if "STUDENT" in {r.name for r in user.roles}:
        own = await repo.get_student_by_user_id(str(user.id))
        if not own or str(own.id) != str(student_id):
            raise ForbiddenError("You may only access your own records.")
        return
    await ensure_student_assigned_to_counsellor(user, student_id, repo)
