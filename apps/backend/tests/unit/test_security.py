import pytest
from app.core.security import (
    verify_password,
    get_password_hash,
    generate_temporary_password,
    create_access_token,
    decode_jwt_token,
    create_refresh_token_pair,
    parse_refresh_token,
    hash_refresh_secret,
)
from app.core.exceptions import AuthenticationError


def test_password_hashing():
    password = "SecretPassword123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_generate_temporary_password_meets_complexity():
    password = generate_temporary_password()
    assert len(password) >= 12
    assert any(c.islower() for c in password)
    assert any(c.isupper() for c in password)
    assert any(c.isdigit() for c in password)


def test_access_token_creation_and_decoding():
    user_id = "test-user-uuid-123"
    roles = ["STUDENT"]
    permissions = ["student.read"]

    token = create_access_token(
        subject=user_id,
        roles=roles,
        permissions=permissions,
        force_password_change=False,
    )
    assert isinstance(token, str)

    payload = decode_jwt_token(token)
    assert payload["sub"] == user_id
    assert payload["roles"] == roles
    assert payload["permissions"] == permissions
    assert payload["force_password_change"] is False
    assert payload["type"] == "access"


def test_invalid_token_decoding_raises():
    with pytest.raises(AuthenticationError):
        decode_jwt_token("invalid.token.string")


def test_refresh_token_pair_round_trip():
    raw_token, token_id, secret_hash, family_id = create_refresh_token_pair()
    parsed_id, secret = parse_refresh_token(raw_token)

    assert parsed_id == token_id
    assert hash_refresh_secret(secret) == secret_hash
    assert family_id  # non-empty


def test_parse_malformed_refresh_token_raises():
    with pytest.raises(AuthenticationError):
        parse_refresh_token("not-a-valid-token")
