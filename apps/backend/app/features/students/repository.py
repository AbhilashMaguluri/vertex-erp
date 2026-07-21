from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.features.students.models import Student, StudentEnrollment, CounsellorAssignment
from app.features.auth.models import User
from app.features.admin.models import Department


class StudentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_student_by_id(self, student_id: str) -> Optional[Student]:
        query = (
            select(Student)
            .where(Student.id == student_id, Student.deleted_at.is_(None))
            .options(
                selectinload(Student.user),
                selectinload(Student.counsellor_assignments).selectinload(CounsellorAssignment.counsellor),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_student_by_roll(self, roll_number: str) -> Optional[Student]:
        query = (
            select(Student)
            .where(Student.roll_number == roll_number.upper(), Student.deleted_at.is_(None))
            .options(selectinload(Student.user))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_students(
        self,
        page: int = 1,
        per_page: int = 20,
        department_id: Optional[str] = None,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
    ) -> Tuple[List[Student], int]:
        query = select(Student).where(Student.deleted_at.is_(None)).options(selectinload(Student.user))
        count_query = select(func.count(Student.id)).where(Student.deleted_at.is_(None))

        if department_id:
            query = query.where(Student.department_id == department_id)
            count_query = count_query.where(Student.department_id == department_id)

        if status:
            query = query.where(Student.status == status.upper())
            count_query = count_query.where(Student.status == status.upper())

        if risk_level:
            query = query.where(Student.risk_level == risk_level.upper())
            count_query = count_query.where(Student.risk_level == risk_level.upper())

        query = query.order_by(Student.roll_number).offset((page - 1) * per_page).limit(per_page)

        students_res = await self.db.execute(query)
        count_res = await self.db.execute(count_query)

        return list(students_res.scalars().all()), count_res.scalar_one()

    async def create_student(self, student: Student) -> Student:
        self.db.add(student)
        await self.db.flush()
        return student
