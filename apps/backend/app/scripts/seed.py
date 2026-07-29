"""Idempotent bootstrap: roles, permissions, the first Admin account, and the
fixed institutional semester catalog (1-1 .. 4-2).

Self-registration has been removed from this application — an institution
with no seeded Admin has no way to create its first user. Run this once per
environment (and again any time ROLE_PERMISSIONS changes) via:

    python -m app.scripts.seed
"""
import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.security import get_password_hash
from app.database import AsyncSessionLocal
from app.features.admin.models import Semester
from app.features.auth.models import Permission, Role, User

# Every feature's models module must be imported at least once so their
# tables are registered on Base.metadata before SQLAlchemy resolves
# cross-feature ForeignKey string references (e.g. User.department_id ->
# "departments.id"). Mirrors the same requirement in alembic/env.py.
from app.features.admin import models as _admin_models  # noqa: F401
from app.features.students import models as _students_models  # noqa: F401
from app.features.students import profile_models as _student_profile_models  # noqa: F401
from app.features.counselling import models as _counselling_models  # noqa: F401
from app.features.attendance import models as _attendance_models  # noqa: F401
from app.features.academics import models as _academics_models  # noqa: F401
from app.features.parents import models as _parents_models  # noqa: F401
from app.features.notifications import models as _notifications_models  # noqa: F401
from app.features.reports import models as _reports_models  # noqa: F401
from app.features.audit import models as _audit_models  # noqa: F401
from app.features.imports import models as _imports_models  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("app.seed")

ALL_PERMISSIONS = [
    ("department.manage", "Create/manage departments"),
    ("section.manage", "Create/manage sections"),
    ("academic.manage", "Create/manage academic years & semesters"),
    ("subject.manage", "Create/manage subjects"),
    ("user.manage", "Create/manage user accounts"),
    ("student.read", "View student profiles & workspace"),
    # Distinct from student.read on purpose: STUDENT holds student.read for
    # their OWN record, so listing many students must be its own permission or
    # a student could enumerate the whole institution. Never grant to STUDENT.
    ("student.caseload.read", "List/browse many students (caseload & directory)"),
    ("student.risk.update", "Update a student's risk flag"),
    # Self-service: a student maintaining their OWN profile. Held only by
    # STUDENT — staff never need it, because every endpoint it guards resolves
    # the student from the caller's own token.
    ("profile.self.manage", "Maintain your own student profile"),
    # Administrative correction of someone else's profile. Deliberately not
    # granted to COUNSELLOR: counsellors read student profiles, never edit them.
    ("student.profile.manage", "Edit another student's profile (admin)"),
    ("counselling.create", "Create counselling sessions"),
    ("counselling.read", "View counselling sessions & follow-ups"),
    ("counselling.update", "Update follow-up status"),
    ("counselling.acknowledge", "Acknowledge a counselling session"),
    ("attendance.create", "Record attendance"),
    ("attendance.read", "View attendance records"),
    ("attendance.correction.create", "Request an attendance correction"),
    ("attendance.correction.approve", "Approve/reject attendance corrections"),
    ("marks.create", "Record marks"),
    ("academics.read", "View marks, backlogs & GPA"),
    ("parent_communication.create", "Log parent communication"),
    ("parent_communication.read", "View parent communication history"),
    ("report.generate", "Generate reports"),
    ("report.download", "View/download report history"),
    ("audit.read", "View audit logs"),
    ("settings.manage", "Manage system settings"),
]

_ALL = [p[0] for p in ALL_PERMISSIONS]

# Fixed institutional semester catalog — not manually created/edited, see
# app/features/admin/models.py::Semester.
FIXED_SEMESTERS = [
    (1, "1-1"), (2, "1-2"),
    (3, "2-1"), (4, "2-2"),
    (5, "3-1"), (6, "3-2"),
    (7, "4-1"), (8, "4-2"),
]

ROLE_PERMISSIONS = {
    "SUPER_ADMIN": _ALL,
    "ADMIN": _ALL,
    "HOD": [
        "student.read", "student.caseload.read", "student.risk.update", "counselling.read",
        "attendance.read", "attendance.correction.approve", "academics.read",
        "parent_communication.read", "report.generate", "report.download", "audit.read",
    ],
    "COUNSELLOR": [
        "student.read", "student.caseload.read", "counselling.create", "counselling.read",
        "counselling.update", "counselling.acknowledge", "parent_communication.create",
        "parent_communication.read", "report.generate", "report.download", "attendance.read",
    ],
    "FACULTY": [
        "attendance.create", "attendance.read", "attendance.correction.create",
        "marks.create", "academics.read", "student.read",
    ],
    "STUDENT": [
        "student.read", "academics.read", "attendance.read", "counselling.acknowledge",
        "report.download", "profile.self.manage",
    ],
}


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        perm_by_name: dict[str, Permission] = {}
        for name, description in ALL_PERMISSIONS:
            result = await db.execute(select(Permission).where(Permission.name == name))
            perm = result.scalar_one_or_none()
            if not perm:
                perm = Permission(name=name, description=description)
                db.add(perm)
                await db.flush()
                logger.info("Created permission: %s", name)
            perm_by_name[name] = perm

        role_by_name: dict[str, Role] = {}
        for role_name, perm_names in ROLE_PERMISSIONS.items():
            result = await db.execute(
                select(Role).where(Role.name == role_name).options(selectinload(Role.permissions))
            )
            role = result.scalar_one_or_none()
            if not role:
                role = Role(name=role_name, description=f"{role_name.replace('_', ' ').title()} role")
                role.permissions = []
                db.add(role)
                await db.flush()
                logger.info("Created role: %s", role_name)
            role.permissions = [perm_by_name[p] for p in perm_names]
            role_by_name[role_name] = role

        await db.commit()

        for number, name in FIXED_SEMESTERS:
            result = await db.execute(select(Semester).where(Semester.number == number))
            if not result.scalar_one_or_none():
                db.add(Semester(number=number, name=name))
                logger.info("Created fixed semester: %s", name)
        await db.commit()

        result = await db.execute(select(User).where(User.email == settings.INITIAL_ADMIN_EMAIL.lower()))
        admin_user = result.scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                email=settings.INITIAL_ADMIN_EMAIL.lower(),
                hashed_password=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                first_name=settings.INITIAL_ADMIN_FIRST_NAME,
                last_name=settings.INITIAL_ADMIN_LAST_NAME,
                is_active=True,
                force_password_change=True,
            )
            admin_user.roles.append(role_by_name["ADMIN"])
            db.add(admin_user)
            await db.commit()
            logger.info(
                "Bootstrap Admin created: %s (temporary password from INITIAL_ADMIN_PASSWORD — change it on first login)",
                settings.INITIAL_ADMIN_EMAIL,
            )
        else:
            logger.info("Bootstrap Admin already exists: %s (left untouched)", settings.INITIAL_ADMIN_EMAIL)


if __name__ == "__main__":
    asyncio.run(seed())
