from datetime import date

import pytest_asyncio

from app.features.admin.models import Department, Section, AcademicYear, Semester, Subject


async def _login(client, email, password):
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def admin_token(client, admin_user):
    return await _login(client, "admin@example.com", "InitialPass123!")


@pytest_asyncio.fixture
async def academic_setup(db_session):
    dept = Department(code="CSE", name="Computer Science")
    dept2 = Department(code="ECE", name="Electronics")
    db_session.add_all([dept, dept2])
    await db_session.flush()

    section = Section(department_id=dept.id, name="CSE-A", batch_year=2026)
    db_session.add(section)

    ay = AcademicYear(name="2026-2027", start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_current=True)
    ay2 = AcademicYear(name="2027-2028", start_date=date(2027, 6, 1), end_date=date(2028, 5, 31), is_current=False)
    db_session.add_all([ay, ay2])
    await db_session.flush()

    semester = Semester(
        academic_year_id=ay.id, number=1, name="Semester 1",
        start_date=date(2026, 6, 1), end_date=date(2026, 11, 30), is_current=True,
    )
    db_session.add(semester)

    subject = Subject(department_id=dept.id, code="CS501", name="Operating Systems", credits=4)
    subject2 = Subject(department_id=dept.id, code="CS502", name="Computer Networks", credits=3)
    db_session.add_all([subject, subject2])
    await db_session.commit()

    return {
        "department": dept, "department2": dept2, "section": section,
        "academic_year": ay, "academic_year2": ay2, "semester": semester,
        "subject": subject, "subject2": subject2,
    }


# --- Departments ---------------------------------------------------------

async def test_admin_can_update_department(client, admin_user, academic_setup):
    token = await admin_token(client, admin_user)
    dept = academic_setup["department"]
    resp = await client.patch(
        f"/api/v1/admin/departments/{dept.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Computer Science & Engineering", "description": "Updated description"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "Computer Science & Engineering"
    assert body["description"] == "Updated description"
    assert body["code"] == "CSE"  # code is immutable


async def test_update_department_not_found(client, admin_user):
    token = await admin_token(client, admin_user)
    resp = await client.patch(
        "/api/v1/admin/departments/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Ghost Department"},
    )
    assert resp.status_code == 404


async def test_non_admin_cannot_update_department(client, db_session, seeded_roles, academic_setup):
    from app.features.auth.models import User
    from app.core.security import get_password_hash

    counsellor = User(
        email="counsellor2@example.com", hashed_password=get_password_hash("Pass1234!"),
        first_name="Coun", last_name="Sellor", is_active=True, force_password_change=False,
    )
    counsellor.roles.append(seeded_roles["COUNSELLOR"])
    db_session.add(counsellor)
    await db_session.commit()

    token = await _login(client, "counsellor2@example.com", "Pass1234!")
    resp = await client.patch(
        f"/api/v1/admin/departments/{academic_setup['department'].id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Hijacked Name"},
    )
    assert resp.status_code == 403


# --- Academic Years --------------------------------------------------------

async def test_admin_can_update_academic_year(client, admin_user, academic_setup):
    token = await admin_token(client, admin_user)
    ay = academic_setup["academic_year"]
    resp = await client.patch(
        f"/api/v1/admin/academic-years/{ay.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_current": False},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_current"] is False


async def test_update_academic_year_rejects_duplicate_name(client, admin_user, academic_setup):
    token = await admin_token(client, admin_user)
    ay = academic_setup["academic_year"]
    other_name = academic_setup["academic_year2"].name
    resp = await client.patch(
        f"/api/v1/admin/academic-years/{ay.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": other_name},
    )
    assert resp.status_code == 409
    assert "already exists" in resp.json()["error"]["message"]


async def test_update_academic_year_rejects_invalid_date_range(client, admin_user, academic_setup):
    token = await admin_token(client, admin_user)
    ay = academic_setup["academic_year"]
    resp = await client.patch(
        f"/api/v1/admin/academic-years/{ay.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"start_date": "2027-01-01", "end_date": "2026-01-01"},
    )
    assert resp.status_code == 422
    assert "after start date" in resp.json()["error"]["message"]


# --- Subjects --------------------------------------------------------------

async def test_admin_can_update_subject(client, admin_user, academic_setup):
    token = await admin_token(client, admin_user)
    subject = academic_setup["subject"]
    resp = await client.patch(
        f"/api/v1/admin/subjects/{subject.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Advanced Operating Systems", "credits": 5},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "Advanced Operating Systems"
    assert body["credits"] == 5


async def test_update_subject_rejects_duplicate_code(client, admin_user, academic_setup):
    token = await admin_token(client, admin_user)
    subject = academic_setup["subject"]
    other_code = academic_setup["subject2"].code
    resp = await client.patch(
        f"/api/v1/admin/subjects/{subject.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": other_code},
    )
    assert resp.status_code == 409
    assert "already exists" in resp.json()["error"]["message"]


async def test_update_subject_rejects_unknown_department(client, admin_user, academic_setup):
    token = await admin_token(client, admin_user)
    subject = academic_setup["subject"]
    resp = await client.patch(
        f"/api/v1/admin/subjects/{subject.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"department_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert resp.status_code == 422


# --- Sections ----------------------------------------------------------------
# Semesters are a fixed, seeded catalog (see app/features/admin/models.py) with
# no create/update API, so there is nothing to exercise here for them.

async def test_admin_can_update_section(client, admin_user, academic_setup):
    token = await admin_token(client, admin_user)
    section = academic_setup["section"]
    dept2 = academic_setup["department2"]
    resp = await client.patch(
        f"/api/v1/admin/sections/{section.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "CSE-B", "department_id": str(dept2.id)},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "CSE-B"
    assert body["department_id"] == str(dept2.id)


# --- Audit trail -------------------------------------------------------------

async def test_update_department_writes_audit_log_with_before_and_after(client, admin_user, academic_setup, db_session):
    from sqlalchemy import select
    from app.features.audit.models import AuditLog

    token = await admin_token(client, admin_user)
    dept = academic_setup["department"]
    resp = await client.patch(
        f"/api/v1/admin/departments/{dept.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Renamed Department"},
    )
    assert resp.status_code == 200, resp.text

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.entity_type == "Department", AuditLog.entity_id == str(dept.id))
    )
    logs = result.scalars().all()
    assert len(logs) == 1
    log = logs[0]
    assert log.action == "UPDATE"
    assert log.user_email == "admin@example.com"
    assert log.changes_json["before"]["name"] == "Computer Science"
    assert log.changes_json["after"]["name"] == "Renamed Department"
