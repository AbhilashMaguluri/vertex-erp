import pytest
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
)
from app.core.exceptions import AuthenticationError


def test_password_hashing():
    password = "SecretPassword123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_access_token_creation_and_decoding():
    user_id = "test-user-uuid-123"
    roles = ["STUDENT"]
    permissions = ["student.read"]

    token = create_access_token(
        subject=user_id,
        roles=roles,
        permissions=permissions,
    )
    assert isinstance(token, str)

    payload = decode_jwt_token(token)
    assert payload["sub"] == user_id
    assert payload["roles"] == roles
    assert payload["permissions"] == permissions
    assert payload["type"] == "access"


def test_invalid_token_decoding():
    with pytest.raises(AuthenticationError):
        decode_jwt_token("invalid.token.string")
