import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.audit import record_audit_log
from app.core.enums import AuditAction
from app.core.exceptions import AuthenticationError, NotFoundError, UnauthorizedError, ValidationError
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token_pair,
    parse_refresh_token,
    hash_refresh_secret,
    generate_password_reset_token,
)
from app.features.auth.models import User, RefreshToken, PasswordResetToken
from app.features.auth.repository import AuthRepository
from app.features.auth.schemas import (
    LoginRequest,
    TokenResponse,
    UserSummary,
    UserProfileResponse,
    ChangePasswordRequest,
    SessionResponse,
)

logger = logging.getLogger("app.auth")

REFRESH_COOKIE_NAME = "refresh_token"


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuthRepository(db)

    # --- helpers -----------------------------------------------------
    @staticmethod
    def _roles_and_permissions(user: User) -> tuple[List[str], List[str]]:
        roles = sorted({r.name for r in user.roles})
        permissions = sorted({p.name for r in user.roles for p in r.permissions})
        return roles, permissions

    def _build_user_summary(self, user: User) -> UserSummary:
        roles, permissions = self._roles_and_permissions(user)
        return UserSummary(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            roles=roles,
            permissions=permissions,
            department_id=str(user.department_id) if user.department_id else None,
            force_password_change=user.force_password_change,
        )

    def _set_refresh_cookie(self, response: Response, raw_token: str, remember_me: bool) -> None:
        days = settings.REMEMBER_ME_REFRESH_TOKEN_EXPIRE_DAYS if remember_me else settings.REFRESH_TOKEN_EXPIRE_DAYS
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=raw_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            domain=settings.COOKIE_DOMAIN,
            path="/",
            max_age=days * 86400,
        )

    def _clear_refresh_cookie(self, response: Response) -> None:
        response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/", domain=settings.COOKIE_DOMAIN)

    async def _issue_session(
        self, user: User, response: Response, request: Optional[Request], remember_me: bool
    ) -> TokenResponse:
        raw_token, token_id, secret_hash, family_id = create_refresh_token_pair()
        days = settings.REMEMBER_ME_REFRESH_TOKEN_EXPIRE_DAYS if remember_me else settings.REFRESH_TOKEN_EXPIRE_DAYS
        expires_at = datetime.now(timezone.utc) + timedelta(days=days)

        ua = (request.headers.get("user-agent") if request else None) or None
        if ua and len(ua) > 255:
            ua = ua[:255]

        ip = (request.client.host if request and request.client else None)
        if ip and len(ip) > 45:
            ip = ip[:45]

        session = RefreshToken(
            id=token_id,
            user_id=user.id,
            secret_hash=secret_hash,
            family_id=family_id,
            remember_me=remember_me,
            user_agent=ua,
            ip_address=ip,
            expires_at=expires_at,
        )
        await self.repo.create_refresh_token(session)
        self._set_refresh_cookie(response, raw_token, remember_me)

        roles, permissions = self._roles_and_permissions(user)
        access_token = create_access_token(
            subject=str(user.id),
            roles=roles,
            permissions=permissions,
            force_password_change=user.force_password_change,
        )

        return TokenResponse(
            access_token=access_token,
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=self._build_user_summary(user),
        )

    # --- public API ----------------------------------------------------
    async def login(self, data: LoginRequest, response: Response, request: Optional[Request] = None) -> TokenResponse:
        user = await self.repo.get_user_by_identifier(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid credentials. Check your username or email and password.")

        if not user.is_active:
            raise UnauthorizedError("This account has been deactivated. Contact your administrator.")

        await self.repo.record_login(user)
        token_response = await self._issue_session(user, response, request, data.remember_me)
        await record_audit_log(
            self.db, user=user, action=AuditAction.LOGIN.value,
            entity_type="User", entity_id=str(user.id), request=request,
        )
        await self.db.commit()
        return token_response

    async def refresh_tokens(
        self, raw_refresh_token: Optional[str], response: Response, request: Optional[Request] = None
    ) -> TokenResponse:
        if not raw_refresh_token:
            raise UnauthorizedError("Refresh token missing")

        token_id, secret = parse_refresh_token(raw_refresh_token)
        token_entity = await self.repo.get_refresh_token_by_id(token_id)
        if not token_entity:
            raise UnauthorizedError("Session not found. Please log in again.")

        if token_entity.used_at is not None or token_entity.revoked_at is not None:
            # Reuse of an already-rotated or revoked token: kill the whole chain.
            await self.repo.revoke_token_family(token_entity.family_id)
            await self.db.commit()
            raise UnauthorizedError("Security check failed: session invalidated. Please log in again.")

        if token_entity.expires_at < datetime.now(timezone.utc):
            raise UnauthorizedError("Session expired. Please log in again.")

        if hash_refresh_secret(secret) != token_entity.secret_hash:
            raise UnauthorizedError("Invalid session token")

        user = await self.repo.get_user_by_id(str(token_entity.user_id))
        if not user or not user.is_active:
            raise UnauthorizedError("Account is inactive")

        await self.repo.mark_token_used(token_entity)

        raw_token, new_token_id, secret_hash, _ = create_refresh_token_pair(family_id=token_entity.family_id)
        days = (
            settings.REMEMBER_ME_REFRESH_TOKEN_EXPIRE_DAYS
            if token_entity.remember_me
            else settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        ua = token_entity.user_agent
        if ua and len(ua) > 255:
            ua = ua[:255]

        ip = (request.client.host if request and request.client else token_entity.ip_address)
        if ip and len(ip) > 45:
            ip = ip[:45]

        new_session = RefreshToken(
            id=new_token_id,
            user_id=user.id,
            secret_hash=secret_hash,
            family_id=token_entity.family_id,
            remember_me=token_entity.remember_me,
            user_agent=ua,
            ip_address=ip,
            expires_at=datetime.now(timezone.utc) + timedelta(days=days),
        )
        await self.repo.create_refresh_token(new_session)
        self._set_refresh_cookie(response, raw_token, token_entity.remember_me)

        roles, permissions = self._roles_and_permissions(user)
        access_token = create_access_token(
            subject=str(user.id),
            roles=roles,
            permissions=permissions,
            force_password_change=user.force_password_change,
        )
        await self.db.commit()

        return TokenResponse(
            access_token=access_token,
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=self._build_user_summary(user),
        )

    async def logout(self, raw_refresh_token: Optional[str], response: Response) -> None:
        if raw_refresh_token:
            try:
                token_id, _ = parse_refresh_token(raw_refresh_token)
                token_entity = await self.repo.get_refresh_token_by_id(token_id)
                if token_entity:
                    await self.repo.revoke_token_family(token_entity.family_id)
                    await self.db.commit()
            except AuthenticationError:
                pass
        self._clear_refresh_cookie(response)

    def get_current_user_profile(self, user: User) -> UserProfileResponse:
        roles, permissions = self._roles_and_permissions(user)
        return UserProfileResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            force_password_change=user.force_password_change,
            department_id=str(user.department_id) if user.department_id else None,
            roles=roles,
            permissions=permissions,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def change_password(
        self,
        user: User,
        data: ChangePasswordRequest,
        current_refresh_token: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> None:
        if not verify_password(data.current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        if data.current_password == data.new_password:
            raise ValidationError("New password must be different from your current password")

        current_token_id = None
        if current_refresh_token:
            try:
                current_token_id, _ = parse_refresh_token(current_refresh_token)
            except AuthenticationError:
                current_token_id = None

        await self.repo.update_password(user, get_password_hash(data.new_password), force_password_change=False)
        # Revoking every other session (keeping only the one making this
        # request) is the consistent policy: this session stays logged in,
        # every other device/browser must re-authenticate.
        await self.repo.revoke_all_user_tokens(str(user.id), except_token_id=current_token_id)
        await record_audit_log(
            self.db, user=user, action=AuditAction.PASSWORD_CHANGE.value,
            entity_type="User", entity_id=str(user.id), request=request,
        )
        await self.db.commit()

    async def initiate_password_reset(self, email: str) -> str:
        generic_message = "If an account with that email exists, a password reset link has been sent."
        user = await self.repo.get_user_by_email(email)
        if not user or not user.is_active:
            return generic_message

        raw_token, token_id, token_hash = generate_password_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        reset_token = PasswordResetToken(
            id=token_id, user_id=user.id, secret_hash=token_hash, expires_at=expires_at
        )
        await self.repo.create_password_reset_token(reset_token)
        await self.db.commit()

        # No SMTP delivery is configured/verified for this deployment; log the
        # link server-side so it is retrievable for support/testing instead of
        # silently disappearing. Never return the token in the API response.
        logger.info("Password reset requested for %s — token(dev-only log)=%s", user.email, raw_token)
        return generic_message

    async def complete_password_reset(self, raw_token: str, new_password: str) -> None:
        try:
            token_id, secret = parse_refresh_token(raw_token)
        except AuthenticationError:
            raise ValidationError("Invalid or expired reset link")

        reset_token = await self.repo.get_password_reset_token_by_id(token_id)
        if (
            not reset_token
            or reset_token.used_at is not None
            or reset_token.expires_at < datetime.now(timezone.utc)
            or hash_refresh_secret(secret) != reset_token.secret_hash
        ):
            raise ValidationError("Invalid or expired reset link")

        user = await self.repo.get_user_by_id(str(reset_token.user_id))
        if not user:
            raise NotFoundError("Account not found")

        await self.repo.update_password(user, get_password_hash(new_password), force_password_change=False)
        await self.repo.mark_reset_token_used(reset_token)
        await self.repo.revoke_all_user_tokens(str(user.id))
        await self.db.commit()

    async def list_my_sessions(self, user: User, current_refresh_token: Optional[str] = None) -> List[SessionResponse]:
        current_token_id = None
        if current_refresh_token:
            try:
                current_token_id, _ = parse_refresh_token(current_refresh_token)
            except AuthenticationError:
                current_token_id = None

        sessions = await self.repo.list_active_sessions(str(user.id))
        return [
            SessionResponse(
                id=str(s.id),
                created_at=s.created_at,
                expires_at=s.expires_at,
                remember_me=s.remember_me,
                user_agent=s.user_agent,
                ip_address=s.ip_address,
                is_current=(current_token_id is not None and str(s.id) == str(current_token_id)),
            )
            for s in sessions
        ]

    async def revoke_my_session(self, user: User, session_id: str) -> None:
        token_entity = await self.repo.get_refresh_token_by_id(session_id)
        if not token_entity or str(token_entity.user_id) != str(user.id):
            raise NotFoundError("Session not found")
        await self.repo.revoke_token(token_entity)
        await self.db.commit()
