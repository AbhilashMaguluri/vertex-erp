from typing import Any, Dict, Optional
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.audit.models import AuditLog
from app.features.auth.models import User


async def record_audit_log(
    db: AsyncSession,
    *,
    user: Optional[User],
    action: str,
    entity_type: str,
    entity_id: str,
    changes: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    """Appends an audit log row in the current transaction. Callers are
    responsible for committing (typically alongside the rest of the
    mutation) so the log only persists if the action actually succeeded."""
    ua = (request.headers.get("user-agent") if request else None) or None
    if ua and len(ua) > 500:
        ua = ua[:500]

    ip = (request.client.host if request and request.client else None)
    if ip and len(ip) > 45:
        ip = ip[:45]

    log = AuditLog(
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        user_role=(user.roles[0].name if user and user.roles else None),
        action=action.upper(),
        entity_type=entity_type,
        entity_id=str(entity_id),
        changes_json=changes,
        ip_address=ip,
        user_agent=ua,
        request_id=(getattr(request.state, "request_id", None) if request else None),
    )
    db.add(log)
    await db.flush()

