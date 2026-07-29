"""Office Import — end-to-end over the API.

Covers the path an administrator actually walks: upload the office sheet,
review what was detected, configure the placement, run the import, and check
that students, counsellors, enrolments, assignments and credentials all exist
afterwards. Re-running the same file must skip rather than duplicate.
"""
import asyncio
import io
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from app.features.admin.models import AcademicYear, Department, Section, Semester
from app.features.auth.models import User
from app.features.students.models import CounsellorAssignment, Student, StudentEnrollment

OFFICE_SHEET = [
    ["VASIREDDY VENKATADRI INSTITUTE OF TECHNOLOGY"],
    ["Department of AI & DS — Counsellor Allotment"],
    [],
    ["S.No", "Student Roll Numbers", "Counselor Name", "Counselor Mobile"],
    [1, "23BQ1A5401 to 23BQ1A5405", "Dr. S. Ravindra", "9440053880"],
    [2, "23BQ1A5406 to 23BQ1A5408", "Dr. K. Satheesh", "9949397532"],
]


def _office_workbook(rows=None) -> bytes:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Counsellor Allotment"
    for row in rows or OFFICE_SHEET:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


async def _admin_token(client):
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": "InitialPass123!"}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def catalog(db_session):
    """The minimum Academic Configuration an import needs to resolve against."""
    department = Department(code="AI&DS", name="Artificial Intelligence & Data Science")
    db_session.add(department)

    academic_year = AcademicYear(
        name="2026-2027", start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_current=True
    )
    db_session.add(academic_year)
    await db_session.flush()

    semester = Semester(number=7, name="4-1", is_current=True)
    db_session.add(semester)
    await db_session.commit()

    return {"department": department, "semester": semester, "academic_year": academic_year}


async def _analyze(client, token, content=None, filename="allotment.xlsx"):
    resp = await client.post(
        "/api/v1/admin/imports/analyze",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                filename,
                content if content is not None else _office_workbook(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _run_to_completion(client, token, batch_id, catalog, **overrides):
    payload = {
        "department_id": str(catalog["department"].id),
        "semester_id": str(catalog["semester"].id),
        "section_name": "A",
        "batch_year": 2023,
        "academic_year_id": str(catalog["academic_year"].id),
        "study_year": 4,
        "reassign_existing_students": False,
        **overrides,
    }
    resp = await client.post(
        f"/api/v1/admin/imports/{batch_id}/execute",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 202, resp.text

    # The import runs as a detached task with its own session; poll the way the
    # wizard does rather than reaching into it.
    for _ in range(100):
        progress = await client.get(
            f"/api/v1/admin/imports/{batch_id}/progress", headers={"Authorization": f"Bearer {token}"}
        )
        assert progress.status_code == 200, progress.text
        if progress.json()["status"] in ("COMPLETED", "FAILED"):
            return progress.json()
        await asyncio.sleep(0.1)
    pytest.fail("The import did not finish within the timeout")


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------

async def test_analysis_expands_ranges_and_writes_no_accounts(client, admin_user, catalog, db_session):
    token = await _admin_token(client)
    preview = await _analyze(client, token)

    assert preview["students_detected"] == 8
    assert preview["importable_students"] == 8
    assert preview["counsellors_detected"] == 2
    assert preview["new_counsellors"] == 2
    assert preview["header_row_number"] == 4
    assert "S.No" in preview["ignored_columns"]
    assert preview["ranges"][0]["student_count"] == 5

    # Nothing is provisioned until the import is actually run.
    assert (await db_session.execute(select(func.count(Student.id)))).scalar_one() == 0


async def test_analysis_suggests_department_and_batch_from_the_roll_number(client, admin_user, catalog):
    token = await _admin_token(client)
    preview = await _analyze(client, token)
    suggestions = {s["field"]: s for s in preview["suggestions"]}

    assert suggestions["batch_year"]["detected_value"] == "2023"
    assert suggestions["batch_year"]["source"] == "DERIVED"
    # Branch code 54 in 23BQ1A5401 resolves to the AI&DS department.
    assert suggestions["department_id"]["detected_id"] == str(catalog["department"].id)
    assert suggestions["semester_id"]["detected_id"] == str(catalog["semester"].id)
    # The office sheet has no section column, so this is the one thing asked for.
    assert suggestions["section_name"]["source"] == "NONE"


async def test_a_file_with_no_roll_column_is_rejected(client, admin_user, catalog):
    token = await _admin_token(client)
    resp = await client.post(
        "/api/v1/admin/imports/analyze",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("staff.xlsx", _office_workbook([["Name", "Designation"], ["Ravindra", "Professor"]]), "application/vnd.ms-excel")},
    )
    assert resp.status_code == 422
    assert "roll-number column" in resp.json()["error"]["message"]


# --------------------------------------------------------------------------
# Execution
# --------------------------------------------------------------------------

async def test_import_creates_students_counsellors_enrolments_and_assignments(
    client, admin_user, catalog, db_session
):
    token = await _admin_token(client)
    preview = await _analyze(client, token)
    progress = await _run_to_completion(client, token, preview["batch_id"], catalog)
    assert progress["status"] == "COMPLETED", progress

    summary = (
        await client.get(
            f"/api/v1/admin/imports/{preview['batch_id']}", headers={"Authorization": f"Bearer {token}"}
        )
    ).json()
    assert summary["students_created"] == 8
    assert summary["counsellors_created"] == 2
    assert summary["assignments_created"] == 8
    assert summary["failed_records"] == 0
    assert summary["students_skipped"] == 0

    students = (await db_session.execute(select(Student))).scalars().all()
    assert {s.roll_number for s in students} == {f"23BQ1A54{n:02d}" for n in range(1, 9)}
    assert all(s.status == "ACTIVE" for s in students)
    assert all(str(s.department_id) == str(catalog["department"].id) for s in students)
    assert all(s.batch_year == 2023 for s in students)

    # Every student gets an academic record and a counsellor.
    assert (await db_session.execute(select(func.count(StudentEnrollment.id)))).scalar_one() == 8
    assert (await db_session.execute(select(func.count(CounsellorAssignment.id)))).scalar_one() == 8

    # The section named on the Configure step was created on demand.
    section = (await db_session.execute(select(Section))).scalars().one()
    assert section.name == "A"
    assert section.batch_year == 2023
    assert section.year == 4


async def test_students_can_log_in_with_their_roll_number(client, admin_user, catalog):
    token = await _admin_token(client)
    preview = await _analyze(client, token)
    await _run_to_completion(client, token, preview["batch_id"], catalog)

    credentials = (
        await client.get(
            f"/api/v1/admin/imports/{preview['batch_id']}/credentials",
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    student = next(c for c in credentials if c["record_type"] == "STUDENT")
    assert student["username"] == student["identifier"]

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": student["username"], "password": student["temporary_password"]},
    )
    assert login.status_code == 200, login.text
    # Bulk-provisioned accounts are gated behind a password change.
    assert login.json()["user"]["force_password_change"] is True
    assert login.json()["user"]["username"] == student["username"]


async def test_counsellors_get_a_username_and_are_reachable_by_email_login(client, admin_user, catalog):
    token = await _admin_token(client)
    preview = await _analyze(client, token)
    await _run_to_completion(client, token, preview["batch_id"], catalog)

    credentials = (
        await client.get(
            f"/api/v1/admin/imports/{preview['batch_id']}/credentials",
            headers={"Authorization": f"Bearer {token}"},
        )
    ).json()
    counsellor = next(c for c in credentials if c["record_type"] == "COUNSELLOR")
    assert counsellor["username"] in ("ravindra.s", "satheesh.k")

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": counsellor["email"], "password": counsellor["temporary_password"]},
    )
    assert login.status_code == 200, login.text
    assert "COUNSELLOR" in login.json()["user"]["roles"]


async def test_reimporting_the_same_file_skips_every_student_and_reuses_the_counsellors(
    client, admin_user, catalog, db_session
):
    token = await _admin_token(client)
    first = await _analyze(client, token)
    await _run_to_completion(client, token, first["batch_id"], catalog)

    second = await _analyze(client, token)
    assert second["duplicate_students"] == 8
    assert second["importable_students"] == 0
    assert second["existing_counsellors"] == 2
    assert second["new_counsellors"] == 0

    await _run_to_completion(client, token, second["batch_id"], catalog)
    summary = (
        await client.get(
            f"/api/v1/admin/imports/{second['batch_id']}", headers={"Authorization": f"Bearer {token}"}
        )
    ).json()
    assert summary["students_created"] == 0
    assert summary["students_skipped"] == 8
    assert summary["counsellors_created"] == 0
    assert summary["counsellors_reused"] == 2

    # Still exactly one account per roll number.
    assert (await db_session.execute(select(func.count(Student.id)))).scalar_one() == 8
    assert (await db_session.execute(select(func.count(CounsellorAssignment.id)))).scalar_one() == 8


async def test_a_completed_batch_cannot_be_run_twice(client, admin_user, catalog):
    token = await _admin_token(client)
    preview = await _analyze(client, token)
    await _run_to_completion(client, token, preview["batch_id"], catalog)

    resp = await client.post(
        f"/api/v1/admin/imports/{preview['batch_id']}/execute",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "department_id": str(catalog["department"].id),
            "semester_id": str(catalog["semester"].id),
            "section_name": "A",
            "batch_year": 2023,
            "reassign_existing_students": False,
        },
    )
    assert resp.status_code == 409


async def test_a_row_with_an_unreadable_range_does_not_stop_the_others(client, admin_user, catalog, db_session):
    token = await _admin_token(client)
    rows = [
        ["S.No", "Student Roll Numbers", "Counselor Name", "Counselor Mobile"],
        [1, "23BQ1A5401 to 23BQ1A5403", "Dr. S. Ravindra", "9440053880"],
        [2, "to be allotted", "Dr. K. Satheesh", "9949397532"],
        [3, "23BQ1A5404", "Dr. S. Ravindra", "9440053880"],
    ]
    preview = await _analyze(client, token, content=_office_workbook(rows))
    assert preview["students_detected"] == 4
    assert any("not a recognisable roll number" in e for e in preview["errors"])

    await _run_to_completion(client, token, preview["batch_id"], catalog)
    assert (await db_session.execute(select(func.count(Student.id)))).scalar_one() == 4


# --------------------------------------------------------------------------
# Artefacts, history and access control
# --------------------------------------------------------------------------

async def test_credentials_and_reports_download_and_can_be_purged(client, admin_user, catalog):
    token = await _admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    preview = await _analyze(client, token)
    batch_id = preview["batch_id"]
    await _run_to_completion(client, token, batch_id, catalog)

    creds = await client.get(f"/api/v1/admin/imports/{batch_id}/credentials.xlsx", headers=headers)
    assert creds.status_code == 200
    assert creds.content[:2] == b"PK"  # a real xlsx is a zip
    assert "attachment" in creds.headers["content-disposition"]

    excel = await client.get(f"/api/v1/admin/imports/{batch_id}/report.xlsx", headers=headers)
    assert excel.status_code == 200 and excel.content[:2] == b"PK"

    pdf = await client.get(f"/api/v1/admin/imports/{batch_id}/report.pdf", headers=headers)
    assert pdf.status_code == 200 and pdf.content[:5] == b"%PDF-"

    purge = await client.delete(f"/api/v1/admin/imports/{batch_id}/credentials", headers=headers)
    assert purge.status_code == 204

    gone = await client.get(f"/api/v1/admin/imports/{batch_id}/credentials.xlsx", headers=headers)
    assert gone.status_code == 404


async def test_history_reports_the_success_rate(client, admin_user, catalog):
    token = await _admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    preview = await _analyze(client, token)
    await _run_to_completion(client, token, preview["batch_id"], catalog)

    history = (await client.get("/api/v1/admin/imports", headers=headers)).json()
    assert history["total_imports"] == 1
    assert history["completed_imports"] == 1
    assert history["success_rate"] == 100.0
    assert history["total_students_created"] == 8
    assert history["items"][0]["file_name"] == "allotment.xlsx"
    assert history["items"][0]["imported_by"] == "Test Admin"


async def test_sample_template_downloads(client, admin_user):
    token = await _admin_token(client)
    resp = await client.get(
        "/api/v1/admin/imports/sample-template.xlsx", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.content[:2] == b"PK"


async def test_imported_accounts_appear_in_the_user_directory(client, admin_user, catalog):
    token = await _admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    preview = await _analyze(client, token)
    await _run_to_completion(client, token, preview["batch_id"], catalog)

    students = (await client.get("/api/v1/admin/users?role=STUDENT&per_page=50", headers=headers)).json()
    assert students["pagination"]["total"] == 8
    assert all(item["username"] for item in students["data"])

    counsellors = (await client.get("/api/v1/admin/users?role=COUNSELLOR", headers=headers)).json()
    assert counsellors["pagination"]["total"] == 2

    # The search box in the directory finds an imported student by roll number.
    found = (await client.get("/api/v1/admin/users?search=23BQ1A5401", headers=headers)).json()
    assert found["pagination"]["total"] == 1


async def test_import_endpoints_require_the_user_manage_permission(client, admin_user, seeded_roles, db_session):
    from app.core.security import get_password_hash

    counsellor = User(
        email="counsellor@example.com",
        hashed_password=get_password_hash("InitialPass123!"),
        first_name="Case",
        last_name="Worker",
        is_active=True,
        force_password_change=False,
    )
    counsellor.roles.append(seeded_roles["COUNSELLOR"])
    db_session.add(counsellor)
    await db_session.commit()

    login = await client.post(
        "/api/v1/auth/login", json={"email": "counsellor@example.com", "password": "InitialPass123!"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assert (await client.get("/api/v1/admin/imports", headers=headers)).status_code == 403
    upload = await client.post(
        "/api/v1/admin/imports/analyze",
        headers=headers,
        files={"file": ("allotment.xlsx", _office_workbook(), "application/vnd.ms-excel")},
    )
    assert upload.status_code == 403
