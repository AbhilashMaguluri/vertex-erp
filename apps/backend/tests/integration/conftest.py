"""Integration test fixtures.

Requires TEST_DATABASE_URL to point at a disposable Postgres database, e.g.
    postgresql+asyncpg://scms_app:<password>@localhost:5432/scms_test

The env var must be set BEFORE app.database is imported anywhere, since the
engine is created at import time from settings.DATABASE_URL — hence the
os.environ assignment happens ahead of every app.* import in this file.
"""
import os

import pytest
import pytest_asyncio

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    pytest.skip(
        "TEST_DATABASE_URL is not set. Point it at a disposable Postgres database to run integration tests.",
        allow_module_level=True,
    )
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from httpx import AsyncClient, ASGITransport  # noqa: E402
from app.database import Base, engine, AsyncSessionLocal  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.features.auth.models import Role, Permission, User  # noqa: E402
from app.scripts.seed import ALL_PERMISSIONS, ROLE_PERMISSIONS  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def _reset_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    from app.middleware.rate_limit import _RATE_LIMIT_DB

    _RATE_LIMIT_DB.clear()
    yield


@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def seeded_roles(db_session):
    perm_by_name = {}
    for name, description in ALL_PERMISSIONS:
        perm = Permission(name=name, description=description)
        db_session.add(perm)
        await db_session.flush()
        perm_by_name[name] = perm

    role_by_name = {}
    for role_name, perm_names in ROLE_PERMISSIONS.items():
        role = Role(name=role_name, description=role_name)
        role.permissions = [perm_by_name[p] for p in perm_names]
        db_session.add(role)
        await db_session.flush()
        role_by_name[role_name] = role

    await db_session.commit()
    return role_by_name


@pytest_asyncio.fixture
async def admin_user(db_session, seeded_roles):
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("InitialPass123!"),
        first_name="Test",
        last_name="Admin",
        is_active=True,
        force_password_change=False,
    )
    user.roles.append(seeded_roles["ADMIN"])
    db_session.add(user)
    await db_session.commit()
    return user
