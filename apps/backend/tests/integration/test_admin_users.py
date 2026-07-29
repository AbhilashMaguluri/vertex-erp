from datetime import date

import pytest_asyncio

from app.features.admin.models import Department, Section, AcademicYear, Semester


async def _login(client, email, password):
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def academic_setup(db_session):
    dept = Department(code="CSE", name="Computer Science")
    db_session.add(dept)
    await db_session.flush()

    section = Section(department_id=dept.id, name="CSE-A", batch_year=2026)
    db_session.add(section)

    ay = AcademicYear(name="2026-2027", start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_current=True)
    db_session.add(ay)
    await db_session.flush()

    semester = Semester(
        academic_year_id=ay.id, number=1, name="Semester 1",
        start_date=date(2026, 6, 1), end_date=date(2026, 11, 30), is_current=True,
    )
    db_session.add(semester)
    await db_session.commit()

    return {"department": dept, "section": section, "semester": semester}


async def admin_token(client, admin_user):
    return await _login(client, "admin@example.com", "InitialPass123!")


async def test_admin_can_create_faculty_with_temp_password_and_forced_change(client, admin_user):
    token = await admin_token(client, admin_user)
    resp = await client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "faculty1@example.com",
            "first_name": "Fac",
            "last_name": "Ulty",
            "role": "FACULTY",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["user"]["force_password_change"] is True
    assert len(body["temporary_password"]) >= 12
    assert body["email_sent"] is False  # no SMTP configured in tests

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "faculty1@example.com", "password": body["temporary_password"]}
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["user"]["force_password_change"] is True


async def test_admin_can_create_student_with_full_provisioning(client, admin_user, academic_setup):
    token = await admin_token(client, admin_user)
    resp = await client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "student1@example.com",
            "first_name": "Stu",
            "last_name": "Dent",
            "role": "STUDENT",
            "department_id": str(academic_setup["department"].id),
            "student_details": {
                "roll_number": "CSE001",
                "registration_number": "REG001",
                "date_of_birth": "2005-01-01",
                "batch_year": 2026,
                "section_id": str(academic_setup["section"].id),
                "semester_id": str(academic_setup["semester"].id),
            },
        },
    )
    assert resp.status_code == 201, resp.text


async def test_non_admin_cannot_create_users(client, db_session, seeded_roles):
    from app.features.auth.models import User
    from app.core.security import get_password_hash

    counsellor = User(
        email="counsellor1@example.com", hashed_password=get_password_hash("Pass1234!"),
        first_name="Coun", last_name="Sellor", is_active=True, force_password_change=False,
    )
    counsellor.roles.append(seeded_roles["COUNSELLOR"])
    db_session.add(counsellor)
    await db_session.commit()

    token = await _login(client, "counsellor1@example.com", "Pass1234!")
    resp = await client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "x@example.com", "first_name": "X", "last_name": "Y", "role": "FACULTY"},
    )
    assert resp.status_code == 403


async def test_admin_deactivate_blocks_login_and_reactivate_restores_it(client, admin_user):
    token = await admin_token(client, admin_user)
    create_resp = await client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "todeactivate@example.com", "first_name": "De", "last_name": "Activate", "role": "FACULTY"},
    )
    user_id = create_resp.json()["user"]["id"]
    temp_password = create_resp.json()["temporary_password"]

    deactivate_resp = await client.post(
        f"/api/v1/admin/users/{user_id}/deactivate", headers={"Authorization": f"Bearer {token}"}
    )
    assert deactivate_resp.status_code == 204

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "todeactivate@example.com", "password": temp_password}
    )
    assert login_resp.status_code == 401

    activate_resp = await client.post(
        f"/api/v1/admin/users/{user_id}/activate", headers={"Authorization": f"Bearer {token}"}
    )
    assert activate_resp.status_code == 204

    login_resp2 = await client.post(
        "/api/v1/auth/login", json={"email": "todeactivate@example.com", "password": temp_password}
    )
    assert login_resp2.status_code == 200


async def test_admin_reset_password_invalidates_old_sessions(client, admin_user):
    token = await admin_token(client, admin_user)
    create_resp = await client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "resetme@example.com", "first_name": "Reset", "last_name": "Me", "role": "FACULTY"},
    )
    user_id = create_resp.json()["user"]["id"]
    old_password = create_resp.json()["temporary_password"]

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "resetme@example.com", "password": old_password}
    )
    old_cookie = login_resp.cookies.get("refresh_token")

    reset_resp = await client.post(
        f"/api/v1/admin/users/{user_id}/reset-password", headers={"Authorization": f"Bearer {token}"}
    )
    assert reset_resp.status_code == 200
    new_password = reset_resp.json()["temporary_password"]
    assert new_password != old_password

    # Old session must no longer be refreshable.
    refresh_resp = await client.post("/api/v1/auth/refresh", cookies={"refresh_token": old_cookie})
    assert refresh_resp.status_code == 401

    # Old password no longer works; new temp password does.
    old_login = await client.post(
        "/api/v1/auth/login", json={"email": "resetme@example.com", "password": old_password}
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login", json={"email": "resetme@example.com", "password": new_password}
    )
    assert new_login.status_code == 200
    assert new_login.json()["user"]["force_password_change"] is True


async def test_admin_force_logout_revokes_all_sessions(client, admin_user):
    token = await admin_token(client, admin_user)
    create_resp = await client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "logoutme@example.com", "first_name": "Log", "last_name": "Outme", "role": "FACULTY"},
    )
    user_id = create_resp.json()["user"]["id"]
    password = create_resp.json()["temporary_password"]

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "logoutme@example.com", "password": password}
    )
    cookie = login_resp.cookies.get("refresh_token")

    force_logout_resp = await client.post(
        f"/api/v1/admin/users/{user_id}/force-logout", headers={"Authorization": f"Bearer {token}"}
    )
    assert force_logout_resp.status_code == 204

    refresh_resp = await client.post("/api/v1/auth/refresh", cookies={"refresh_token": cookie})
    assert refresh_resp.status_code == 401


# Bulk provisioning moved to the Office Import module; its coverage lives in
# tests/integration/test_office_import.py.
