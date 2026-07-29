from app.core.security import get_password_hash
from app.features.auth.models import User


async def test_login_success(client, admin_user):
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": "InitialPass123!"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == "admin@example.com"
    assert data["user"]["force_password_change"] is False
    assert "access_token" in data
    assert "refresh_token" in resp.cookies


async def test_login_wrong_password_rejected(client, admin_user):
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": "WrongPassword!"}
    )
    assert resp.status_code == 401


async def test_login_unknown_email_rejected(client, seeded_roles):
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "WhoKnows123!"}
    )
    assert resp.status_code == 401


async def test_new_user_must_change_password_before_using_app(client, db_session, seeded_roles):
    user = User(
        email="newbie@example.com",
        hashed_password=get_password_hash("TempPass123!"),
        first_name="New",
        last_name="User",
        is_active=True,
        force_password_change=True,
    )
    user.roles.append(seeded_roles["FACULTY"])
    db_session.add(user)
    await db_session.commit()

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "newbie@example.com", "password": "TempPass123!"}
    )
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert body["user"]["force_password_change"] is True
    token = body["access_token"]

    # A real business endpoint is blocked server-side while the flag is set.
    blocked_resp = await client.get(
        "/api/v1/notifications", headers={"Authorization": f"Bearer {token}"}
    )
    assert blocked_resp.status_code == 403
    assert blocked_resp.json()["error"]["code"] == "PASSWORD_CHANGE_REQUIRED"

    # /auth/me must still work — the frontend needs it to detect the flag.
    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200

    change_resp = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "TempPass123!", "new_password": "BrandNewPass123!"},
    )
    assert change_resp.status_code == 204

    relogin_resp = await client.post(
        "/api/v1/auth/login", json={"email": "newbie@example.com", "password": "BrandNewPass123!"}
    )
    assert relogin_resp.status_code == 200
    assert relogin_resp.json()["user"]["force_password_change"] is False

    unblocked_resp = await client.get(
        "/api/v1/notifications",
        headers={"Authorization": f"Bearer {relogin_resp.json()['access_token']}"},
    )
    assert unblocked_resp.status_code == 200


async def test_refresh_rotates_and_detects_reuse(client, admin_user):
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": "InitialPass123!"}
    )
    old_cookie = login_resp.cookies.get("refresh_token")

    refresh_resp = await client.post("/api/v1/auth/refresh", cookies={"refresh_token": old_cookie})
    assert refresh_resp.status_code == 200
    new_cookie = refresh_resp.cookies.get("refresh_token")
    assert new_cookie != old_cookie

    # Reusing the rotated-out token is a reuse-detection event.
    reuse_resp = await client.post("/api/v1/auth/refresh", cookies={"refresh_token": old_cookie})
    assert reuse_resp.status_code == 401

    # Reuse must revoke the whole family, including the token issued by refresh above.
    followup_resp = await client.post("/api/v1/auth/refresh", cookies={"refresh_token": new_cookie})
    assert followup_resp.status_code == 401


async def test_logout_clears_session(client, admin_user):
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": "InitialPass123!"}
    )
    cookie = login_resp.cookies.get("refresh_token")

    logout_resp = await client.post("/api/v1/auth/logout", cookies={"refresh_token": cookie})
    assert logout_resp.status_code == 204

    refresh_resp = await client.post("/api/v1/auth/refresh", cookies={"refresh_token": cookie})
    assert refresh_resp.status_code == 401


async def test_deactivated_user_cannot_login(client, db_session, seeded_roles):
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("Pass1234!"),
        first_name="In",
        last_name="Active",
        is_active=False,
        force_password_change=False,
    )
    user.roles.append(seeded_roles["STUDENT"])
    db_session.add(user)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login", json={"email": "inactive@example.com", "password": "Pass1234!"}
    )
    assert resp.status_code == 401


async def test_unauthenticated_request_rejected(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_role_without_permission_gets_403(client, db_session, seeded_roles):
    user = User(
        email="student@example.com",
        hashed_password=get_password_hash("Pass1234!"),
        first_name="Stu",
        last_name="Dent",
        is_active=True,
        force_password_change=False,
    )
    user.roles.append(seeded_roles["STUDENT"])
    db_session.add(user)
    await db_session.commit()

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "student@example.com", "password": "Pass1234!"}
    )
    token = login_resp.json()["access_token"]

    # user.manage is Admin-only; a Student must be forbidden, not crash.
    resp = await client.get(
        "/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403
