from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.scoping import is_assignment_scoped_counsellor
from app.features.auth.models import User
from app.features.auth.repository import AuthRepository
from app.features.students.repository import StudentRepository
from app.features.search.schemas import SearchResultItem

_MIN_QUERY_LENGTH = 2
_MAX_RESULTS_PER_TYPE = 6


class SearchService:
    """A single endpoint, scoped entirely by what the caller's permissions
    and assignments already allow them to see elsewhere in the app — it
    never exposes an entity a dedicated page wouldn't also show this user."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.student_repo = StudentRepository(db)
        self.auth_repo = AuthRepository(db)

    async def search(self, query: str, user: User) -> List[SearchResultItem]:
        query = query.strip()
        if len(query) < _MIN_QUERY_LENGTH:
            return []

        permissions = {p.name for role in user.roles for p in role.permissions}
        results: List[SearchResultItem] = []

        if "student.read" in permissions:
            students = await self.student_repo.search_students(query, limit=_MAX_RESULTS_PER_TYPE)
            if is_assignment_scoped_counsellor(user):
                students = [
                    s for s in students
                    if any(a.counsellor_id == user.id and a.effective_to is None for a in s.counsellor_assignments)
                ]
            for s in students:
                results.append(
                    SearchResultItem(
                        type="student",
                        id=str(s.id),
                        title=s.user.full_name if s.user else s.roll_number,
                        subtitle=f"Roll {s.roll_number}",
                        url=f"/students/{s.id}/workspace",
                    )
                )

        if "user.manage" in permissions:
            users, _total = await self.auth_repo.list_users(search=query, offset=0, limit=_MAX_RESULTS_PER_TYPE)
            for u in users:
                results.append(
                    SearchResultItem(
                        type="user",
                        id=str(u.id),
                        title=u.full_name,
                        subtitle=u.email,
                        url="/admin/users",
                    )
                )

        return results
