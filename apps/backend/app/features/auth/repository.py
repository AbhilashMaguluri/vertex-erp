from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.features.auth.models import User, Role, Permission, RefreshToken, PasswordResetToken


def _with_roles(query):
    return query.options(selectinload(User.roles).selectinload(Role.permissions))


class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Users -----------------------------------------------------------
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        query = _with_roles(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        query = _with_roles(select(User).where(User.email == email.lower(), User.deleted_at.is_(None)))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_identifier(self, identifier: str) -> Optional[User]:
        """Resolve a login identifier: either the email address or the short
        username Office Import issues (a student's is their roll number).

        Both columns are unique, so at most one row can match either way.
        """
        value = (identifier or "").strip().lower()
        if not value:
            return None
        query = _with_roles(
            select(User).where(
                or_(func.lower(User.email) == value, func.lower(User.username) == value),
                User.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def list_users(
        self,
        role: Optional[str] = None,
        department_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[User], int]:
        query = _with_roles(select(User).where(User.deleted_at.is_(None)))
        count_query = select(func.count(func.distinct(User.id))).where(User.deleted_at.is_(None))

        if role:
            query = query.join(User.roles).where(Role.name == role.upper())
            count_query = count_query.join(User.roles).where(Role.name == role.upper())
        if department_id:
            query = query.where(User.department_id == department_id)
            count_query = count_query.where(User.department_id == department_id)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
            count_query = count_query.where(User.is_active == is_active)
        if search:
            like = f"%{search.lower()}%"
            cond = (func.lower(User.email).like(like)) | (func.lower(User.first_name + " " + User.last_name).like(like))
            query = query.where(cond)
            count_query = count_query.where(cond)

        total = (await self.db.execute(count_query)).scalar_one()
        query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.unique().scalars().all()), total

    async def set_active(self, user: User, is_active: bool) -> None:
        user.is_active = is_active
        await self.db.flush()

    async def update_password(self, user: User, hashed_password: str, force_password_change: bool) -> None:
        user.hashed_password = hashed_password
        user.force_password_change = force_password_change
        await self.db.flush()

    async def record_login(self, user: User) -> None:
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

    # --- Roles & Permissions ----------------------------------------------
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        query = select(Role).where(Role.name == name.upper())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_roles(self) -> List[Role]:
        result = await self.db.execute(select(Role))
        return list(result.scalars().all())

    async def get_permission_by_name(self, name: str) -> Optional[Permission]:
        result = await self.db.execute(select(Permission).where(Permission.name == name))
        return result.scalar_one_or_none()

    # --- Refresh tokens / sessions -----------------------------------------
    async def create_refresh_token(self, token: RefreshToken) -> RefreshToken:
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_refresh_token_by_id(self, token_id: str) -> Optional[RefreshToken]:
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.id == token_id))
        return result.scalar_one_or_none()

    async def list_active_sessions(self, user_id: str) -> List[RefreshToken]:
        now = datetime.now(timezone.utc)
        query = (
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.used_at.is_(None),
                RefreshToken.expires_at > now,
            )
            .order_by(RefreshToken.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def revoke_token_family(self, family_id: str) -> None:
        query = select(RefreshToken).where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        result = await self.db.execute(query)
        now = datetime.now(timezone.utc)
        for token in result.scalars().all():
            token.revoked_at = now
        await self.db.flush()

    async def revoke_all_user_tokens(self, user_id: str, except_token_id: Optional[str] = None) -> None:
        query = select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        result = await self.db.execute(query)
        now = datetime.now(timezone.utc)
        for token in result.scalars().all():
            if except_token_id and str(token.id) == str(except_token_id):
                continue
            token.revoked_at = now
        await self.db.flush()

    async def revoke_token(self, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def mark_token_used(self, token: RefreshToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        await self.db.flush()

    # --- Password reset ------------------------------------------------
    async def create_password_reset_token(self, token: PasswordResetToken) -> PasswordResetToken:
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_password_reset_token_by_id(self, token_id: str) -> Optional[PasswordResetToken]:
        result = await self.db.execute(select(PasswordResetToken).where(PasswordResetToken.id == token_id))
        return result.scalar_one_or_none()

    async def mark_reset_token_used(self, token: PasswordResetToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        await self.db.flush()
