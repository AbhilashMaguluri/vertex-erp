import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
from app.features.auth.models import RefreshToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


hash_password = get_password_hash


def create_access_token(subject: str, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def generate_token_family_id() -> str:
    return str(uuid.uuid4())


def create_refresh_token(
    user_id: str, family_id: Optional[str] = None, expires_at: Optional[datetime] = None
) -> Tuple[str, RefreshToken]:
    if not family_id:
        family_id = generate_token_family_id()

    token_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    if not expires_at:
        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "jti": token_id,
        "sub": str(user_id),
        "family_id": family_id,
        "iat": now,
        "exp": expires_at,
        "type": "refresh",
    }

    raw_token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    refresh_entity = RefreshToken(
        id=uuid.UUID(token_id),
        user_id=uuid.UUID(user_id),
        family_id=uuid.UUID(family_id),
        expires_at=expires_at,
        is_revoked=False,
        is_used=False,
    )

    return raw_token, refresh_entity


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


decode_jwt_token = decode_token
