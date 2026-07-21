import hashlib
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.features.auth.models import User, Role, Permission, RefreshToken, PasswordResetToken


class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        query = (
            select(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        query = (
            select(User)
            .where(User.email == email.lower(), User.deleted_at.is_(None))
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        query = select(Role).where(Role.name == name.upper())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def save_refresh_token(
        self, user_id: str, token_str: str, family_id: str, expires_at: datetime
    ) -> RefreshToken:
        token_hash = hashlib.sha256(token_str.encode()).hexdigest()
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_refresh_token(self, token_str: str) -> Optional[RefreshToken]:
        token_hash = hashlib.sha256(token_str.encode()).hexdigest()
        query = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def revoke_token_family(self, family_id: str):
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id)
            .values(is_revoked=True)
        )
        await self.db.execute(stmt)

    async def revoke_all_user_tokens(self, user_id: str):
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.db.execute(stmt)

    async def create_password_reset_token(self, user_id: str, token_str: str, expires_at: datetime) -> PasswordResetToken:
        token_hash = hashlib.sha256(token_str.encode()).hexdigest()
        token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_password_reset_token(self, token_str: str) -> Optional[PasswordResetToken]:
        token_hash = hashlib.sha256(token_str.encode()).hexdigest()
        query = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.is_used.is_(False),
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
