import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.features.reach_out.schemas import CounsellorContactProfileUpdate
from pydantic import ValidationError

requires_db = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not set. Point it at a disposable Postgres database to run API integration tests."
)

@requires_db
@pytest.mark.asyncio
async def test_reach_out_health_and_policy():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/reach-out/channel-policy")
        assert response.status_code == 200
        data = response.json()
        assert "whatsapp_enabled" in data
        assert "email_enabled" in data

@requires_db
@pytest.mark.asyncio
async def test_emergency_contacts_public_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/reach-out/emergency-contacts")
        assert response.status_code == 200
        contacts = response.json()
        assert isinstance(contacts, list)

def test_pydantic_validation_invalid_url():
    with pytest.raises(ValidationError):
        CounsellorContactProfileUpdate(maps_url="invalid_url_without_http")

def test_pydantic_validation_invalid_phone():
    with pytest.raises(ValidationError):
        CounsellorContactProfileUpdate(office_phone="abc1234")

def test_pydantic_validation_valid_inputs():
    valid = CounsellorContactProfileUpdate(
        office_phone="+91 863 2288200",
        maps_url="https://maps.google.com/?q=VVIT",
        linkedin_url="https://linkedin.com/in/counsellor"
    )
    assert valid.office_phone == "+91 863 2288200"
    assert valid.maps_url == "https://maps.google.com/?q=VVIT"
