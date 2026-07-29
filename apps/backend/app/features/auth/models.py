import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.shared.models.base import AuditMixin, TimestampMixin

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    roles: Mapped[List["Role"]] = relationship("Role", secondary=role_permissions, back_populates="permissions")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    users: Mapped[List["User"]] = relationship("User", secondary=user_roles, back_populates="roles")
    permissions: Mapped[List[Permission]] = relationship("Permission", secondary=role_permissions, back_populates="roles")


class User(Base, AuditMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    # The short identifier the institution already uses for this person — a
    # student's roll number, a staff member's `firstname.initial`. Login accepts
    # it in place of the email so a bulk-provisioned student can sign in with
    # the roll number printed on their credential slip. Nullable because
    # accounts predating Office Import (and the bootstrap Admin) have none.
    username: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    department_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        # use_alter breaks the users<->departments circular FK (Department.hod_user_id
        # references users.id): this constraint is deferred to a post-creation
        # ALTER TABLE so SQLAlchemy's DDL sorter (create_all/drop_all) doesn't raise
        # CircularDependencyError. Matches the equivalent split already applied by
        # hand in the initial Alembic migration.
        ForeignKey("departments.id", ondelete="SET NULL", use_alter=True, name="fk_users_department_id_departments"),
        nullable=True,
    )

    # Provisioning & first-login flow. Every account created by an Admin
    # starts with this set to True; login stays gated to /auth/change-password
    # until it is cleared. Never settable by the user themselves except by
    # successfully changing their password.
    force_password_change: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    roles: Mapped[List[Role]] = relationship("Role", secondary=user_roles, back_populates="users")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan", foreign_keys="RefreshToken.user_id"
    )

    @property
    def full_name(self) -> str:
        # Stripped: a staff name written as a single word ("Ravindra") has no
        # surname to append, and must not render with a trailing space.
        return f"{self.first_name} {self.last_name}".strip()


class RefreshToken(Base, TimestampMixin):
    """A row per issued refresh token == a browser session. Rotation-family
    based reuse detection: reusing an already-rotated (used) or revoked token
    revokes every token in that family, killing the whole session chain."""

    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    secret_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    family_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    remember_me: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="refresh_tokens", foreign_keys=[user_id])

    @property
    def is_active(self) -> bool:
        return (
            self.used_at is None
            and self.revoked_at is None
            and self.expires_at > datetime.now(timezone.utc)
        )


class PasswordResetToken(Base, TimestampMixin):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    secret_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
