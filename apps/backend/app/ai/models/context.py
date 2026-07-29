"""Rich context models that travel with every Vertex request.

The context tells Vertex *who* is asking, *where* they are in the ERP, and
what *mode* to operate in — enabling page-aware, role-aware responses without
the user having to repeat themselves.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class UserContext(BaseModel):
    """Identity and permissions of the current user."""

    id: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None  # "STUDENT", "COUNSELLOR", "FACULTY", "HOD", "ADMIN"
    department: Optional[str] = None
    permissions: List[str] = []


class PageContext(BaseModel):
    """Where the user currently is inside the ERP."""

    page: str = "unknown"
    student_id: Optional[str] = None
    params: Dict[str, str] = {}


class VertexContext(BaseModel):
    """Combined context sent with every message to Vertex."""

    user: UserContext = UserContext()
    page: PageContext = PageContext()
    mode: str = "guest"  # guest | student | counsellor | faculty | hod | admin
    timestamp: Optional[str] = None
