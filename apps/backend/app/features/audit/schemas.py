from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    changes_json: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    request_id: Optional[str] = None

    class Config:
        from_attributes = True


class SystemSettingResponse(BaseModel):
    section: str
    key: str
    value: Dict[str, Any]
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SystemSettingUpdateRequest(BaseModel):
    value: Dict[str, Any]
