from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_token_family_id,
)
from app.features.auth.models import User, RefreshToken, PasswordResetToken
from app.features.auth.repository import AuthRepository
from app.features.auth.schemas import (
    LoginRequest,
    TokenResponse,
    UserProfileResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuthRepository(db)

    async def login(self, data: LoginRequest, response: Response) -> TokenResponse:
        user = await self.repo.get_user_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("User account is inactive. Please contact administration.")

        family_id = generate_token_family_id()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # Create refresh token entity
        raw_refresh_token, refresh_entity = create_refresh_token(
            str(user.id), family_id=family_id, expires_at=expires_at
        )
        await self.repo.create_refresh_token(refresh_entity)
        await self.db.commit()

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email, "roles": [r.name for r in user.roles]},
        )

        response.set_cookie(
            key="refresh_token",
            value=raw_refresh_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_tokens(self, refresh_token_str: Optional[str], response: Response) -> TokenResponse:
        if not refresh_token_str:
            raise UnauthorizedError("Refresh token missing")

        payload = decode_token(refresh_token_str)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid refresh token")

        token_id = payload.get("jti")
        family_id = payload.get("family_id")
        user_id = payload.get("sub")

        token_entity = await self.repo.get_refresh_token_by_id(token_id)
        if not token_entity:
            raise UnauthorizedError("Refresh token not found")

        # Security Check: Token Reuse Detection
        if token_entity.is_revoked or token_entity.is_used:
            # Revoke entire token family to mitigate token theft
            await self.repo.revoke_token_family(family_id)
            await self.db.commit()
            raise UnauthorizedError("Security violation: Token reuse detected. All sessions revoked.")

        if token_entity.expires_at < datetime.now(timezone.utc):
            raise UnauthorizedError("Refresh token expired")

        # Mark used
        token_entity.is_used = True

        user = await self.repo.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User account inactive or missing")

        # Issue new token pair
        new_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_raw_refresh, new_refresh_entity = create_refresh_token(
            user_id=str(user.id), family_id=family_id, expires_at=new_expires_at
        )
        await self.repo.create_refresh_token(new_refresh_entity)
        await self.db.commit()

        new_access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email, "roles": [r.name for r in user.roles]},
        )

        response.set_cookie(
            key="refresh_token",
            value=new_raw_refresh,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        )

        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(self, refresh_token_str: Optional[str], response: Response):
        if refresh_token_str:
            payload = decode_token(refresh_token_str)
            if payload and payload.get("family_id"):
                await self.repo.revoke_token_family(payload["family_id"])
                await self.db.commit()

        response.delete_cookie(key="refresh_token")

    async def get_current_user_profile(self, user_id: str) -> UserProfileResponse:
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User profile not found")

        roles = [r.name for r in user.roles]
        permissions = list({p.name for r in user.roles for p in r.permissions})

        return UserProfileResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            is_verified=user.is_verified,
            department_id=str(user.department_id) if user.department_id else None,
            roles=roles,
            permissions=permissions,
            created_at=user.created_at,
        )
