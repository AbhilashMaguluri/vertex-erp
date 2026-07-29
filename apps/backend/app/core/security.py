import hashlib
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.exceptions import AuthenticationError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# Backwards-friendly alias used in a couple of call sites
hash_password = get_password_hash


def generate_student_default_password(roll_number: str) -> str:
    """The institution's standard default password for student accounts:
    `<RollNumber>@vvit.net`. Admins may still override it at creation time."""
    return f"{roll_number.strip().upper()}@vvit.net"


def generate_temporary_password(length: int = 14) -> str:
    """Cryptographically random temporary password guaranteed to contain
    at least one lowercase, uppercase, digit and symbol character."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        candidate = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in candidate)
            and any(c.isupper() for c in candidate)
            and any(c.isdigit() for c in candidate)
            and any(c in "!@#$%^&*" for c in candidate)
        ):
            return candidate


# Characters a person reliably mistypes when reading a password off a printed
# list: 0/O, 1/l/I. Excluded so a bulk-issued credential sheet does not generate
# a queue of "it says my password is wrong" tickets on day one.
_AMBIGUOUS_CHARACTERS = "0O1lI"
_READABLE_LOWER = "".join(c for c in string.ascii_lowercase if c not in _AMBIGUOUS_CHARACTERS)
_READABLE_UPPER = "".join(c for c in string.ascii_uppercase if c not in _AMBIGUOUS_CHARACTERS)
_READABLE_DIGITS = "".join(c for c in string.digits if c not in _AMBIGUOUS_CHARACTERS)
_READABLE_SYMBOLS = "@#$%&*+?"


def generate_readable_password(length: int = 8) -> str:
    """A short, transcribable temporary password for bulk-provisioned accounts.

    Same guarantee as `generate_temporary_password` — one character from each
    class, drawn from `secrets` — but built from an alphabet with the
    look-alike characters removed, because these are handed out on paper.
    Every account issued one is created with force_password_change=True, so it
    is only ever used once.
    """
    if length < 4:
        raise ValueError("A readable password needs at least 4 characters")

    pools = (_READABLE_LOWER, _READABLE_UPPER, _READABLE_DIGITS, _READABLE_SYMBOLS)
    characters = [secrets.choice(pool) for pool in pools]
    everything = "".join(pools)
    characters += [secrets.choice(everything) for _ in range(length - len(pools))]
    # Shuffle in place with secrets, not random.shuffle, so the guaranteed
    # characters do not always land in the first four positions.
    for i in range(len(characters) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        characters[i], characters[j] = characters[j], characters[i]
    return "".join(characters)


def create_access_token(
    subject: str,
    roles: Optional[List[str]] = None,
    permissions: Optional[List[str]] = None,
    force_password_change: bool = False,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "roles": roles or [],
        "permissions": permissions or [],
        "force_password_change": force_password_change,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise AuthenticationError("Invalid or expired token")


# Alias kept for readability at call sites that only ever handle access tokens
decode_access_token = decode_jwt_token


def generate_token_family_id() -> str:
    return str(uuid.uuid4())


def hash_refresh_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def create_refresh_token_pair(
    family_id: Optional[str] = None,
) -> Tuple[str, str, str, str]:
    """Generates a new opaque refresh token.

    The token handed to the client is `"<token_id>.<secret>"`. Only a hash of
    the secret is stored server-side, so a leaked database row cannot be used
    to forge a valid refresh token (the raw secret never touches the DB).

    Returns: (raw_token, token_id, secret_hash, family_id)
    """
    token_id = str(uuid.uuid4())
    secret = secrets.token_urlsafe(48)
    raw_token = f"{token_id}.{secret}"
    return raw_token, token_id, hash_refresh_secret(secret), family_id or generate_token_family_id()


def parse_refresh_token(raw_token: str) -> Tuple[str, str]:
    """Splits a raw refresh token into (token_id, secret). Raises
    AuthenticationError if the token is not well-formed."""
    if not raw_token or "." not in raw_token:
        raise AuthenticationError("Malformed refresh token")
    token_id, _, secret = raw_token.partition(".")
    if not token_id or not secret:
        raise AuthenticationError("Malformed refresh token")
    return token_id, secret


def generate_password_reset_token() -> Tuple[str, str, str]:
    """Returns (raw_token, token_id, token_hash) for a password reset link."""
    token_id = str(uuid.uuid4())
    secret = secrets.token_urlsafe(32)
    raw_token = f"{token_id}.{secret}"
    return raw_token, token_id, hash_refresh_secret(secret)
