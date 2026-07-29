import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit_log
from app.core.email import send_email
from app.core.enums import AuditAction
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.pagination import PaginatedResponse, PaginationParams
from app.core.security import get_password_hash, generate_temporary_password, generate_student_default_password
from app.features.admin.models import Department, Section, AcademicYear, Subject
from app.features.admin.repository import AdminRepository
from app.features.admin.schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    AcademicYearCreate,
    AcademicYearUpdate,
    AcademicYearResponse,
    SemesterResponse,
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
)
from app.features.auth.models import User
from app.features.auth.repository import AuthRepository
from app.features.auth.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserProfileResponse,
    UserListItemResponse,
    AdminCreateUserResponse,
    AdminResetPasswordResponse,
    AssignCounsellorRequest,
    SessionResponse,
    StudentProvisionDetails,
)
from app.features.auth.service import AuthService
from app.features.students.models import Student, CounsellorAssignment
from app.features.students.repository import StudentRepository

class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminRepository(db)
        self.auth_repo = AuthRepository(db)
        self.student_repo = StudentRepository(db)

    # Department Services
    async def create_department(self, data: DepartmentCreate, creator_id: str) -> DepartmentResponse:
        dept = Department(
            code=data.code.upper(),
            name=data.name,
            description=data.description,
            hod_user_id=data.hod_user_id,
            created_by=creator_id,
        )
        await self.repo.create_department(dept)
        await self.db.commit()
        return DepartmentResponse.model_validate(dept)

    async def list_departments(self) -> List[DepartmentResponse]:
        depts = await self.repo.list_departments()
        return [DepartmentResponse.model_validate(d) for d in depts]

    async def update_department(
        self, department_id: str, data: DepartmentUpdate, actor: Optional[User] = None, request: Optional[Request] = None
    ) -> DepartmentResponse:
        dept = await self.repo.get_department_by_id(department_id)
        if not dept:
            raise NotFoundError("Department not found")

        updates = data.model_dump(exclude_unset=True)
        before: dict = {}
        after: dict = {}

        if "name" in updates and updates["name"] != dept.name:
            before["name"], after["name"] = dept.name, updates["name"]
            dept.name = updates["name"]
        if "description" in updates and updates["description"] != dept.description:
            before["description"], after["description"] = dept.description, updates["description"]
            dept.description = updates["description"]
        if "hod_user_id" in updates and updates["hod_user_id"] != (str(dept.hod_user_id) if dept.hod_user_id else None):
            before["hod_user_id"] = str(dept.hod_user_id) if dept.hod_user_id else None
            after["hod_user_id"] = updates["hod_user_id"]
            dept.hod_user_id = updates["hod_user_id"]

        if after:
            try:
                await self.db.flush()
            except IntegrityError as exc:
                await self.db.rollback()
                raise ConflictError("Could not update department — a conflicting or invalid reference was found.") from exc

            await record_audit_log(
                self.db, user=actor, action=AuditAction.UPDATE.value,
                entity_type="Department", entity_id=department_id,
                changes={"before": before, "after": after}, request=request,
            )
            await self.db.commit()

        return DepartmentResponse.model_validate(dept)

    # Section Services
    async def create_section(self, data: SectionCreate, creator_id: str) -> SectionResponse:
        dept = await self.repo.get_department_by_id(data.department_id)
        if not dept:
            raise ValidationError(f"Department '{data.department_id}' not found")

        existing = await self.repo.get_section_by_name(data.department_id, data.year, data.name)
        if existing:
            raise ConflictError(f"Section '{data.name}' already exists for this department and year")

        section = Section(
            department_id=data.department_id,
            name=data.name,
            year=data.year,
            batch_year=data.batch_year,
            created_by=creator_id,
        )
        await self.repo.create_section(section)
        await self.db.commit()
        return SectionResponse.model_validate(section)

    async def list_sections(self, department_id: Optional[str] = None) -> List[SectionResponse]:
        sections = await self.repo.list_sections(department_id)
        return [SectionResponse.model_validate(s) for s in sections]

    async def update_section(
        self, section_id: str, data: SectionUpdate, actor: Optional[User] = None, request: Optional[Request] = None
    ) -> SectionResponse:
        section = await self.repo.get_section_by_id(section_id)
        if not section:
            raise NotFoundError("Section not found")

        updates = data.model_dump(exclude_unset=True)
        before: dict = {}
        after: dict = {}

        if "department_id" in updates and updates["department_id"] != str(section.department_id):
            dept = await self.repo.get_department_by_id(updates["department_id"])
            if not dept:
                raise ValidationError(f"Department '{updates['department_id']}' not found")
            before["department_id"], after["department_id"] = str(section.department_id), updates["department_id"]
            section.department_id = updates["department_id"]

        next_name = updates.get("name", section.name)
        next_year = updates.get("year", section.year)
        if ("name" in updates and updates["name"] != section.name) or ("year" in updates and updates["year"] != section.year):
            existing = await self.repo.get_section_by_name(str(section.department_id), next_year, next_name, exclude_id=section_id)
            if existing:
                raise ConflictError(f"Section '{next_name}' already exists for this department and year")

        if "name" in updates and updates["name"] != section.name:
            before["name"], after["name"] = section.name, updates["name"]
            section.name = updates["name"]
        if "year" in updates and updates["year"] != section.year:
            before["year"], after["year"] = section.year, updates["year"]
            section.year = updates["year"]
        if "batch_year" in updates and updates["batch_year"] != section.batch_year:
            before["batch_year"], after["batch_year"] = section.batch_year, updates["batch_year"]
            section.batch_year = updates["batch_year"]

        if after:
            try:
                await self.db.flush()
            except IntegrityError as exc:
                await self.db.rollback()
                raise ConflictError("Could not update section — a conflicting or invalid reference was found.") from exc

            await record_audit_log(
                self.db, user=actor, action=AuditAction.UPDATE.value,
                entity_type="Section", entity_id=section_id,
                changes={"before": before, "after": after}, request=request,
            )
            await self.db.commit()

        return SectionResponse.model_validate(section)

    async def delete_section(self, section_id: str, actor: Optional[User] = None, request: Optional[Request] = None) -> None:
        section = await self.repo.get_section_by_id(section_id)
        if not section:
            raise NotFoundError("Section not found")

        enrolled_count = await self.repo.count_active_enrollments_for_section(section_id)
        if enrolled_count > 0:
            raise ConflictError(
                f"Cannot delete section '{section.name}' — {enrolled_count} student(s) are enrolled in it."
            )

        section.deleted_at = datetime.now(timezone.utc)
        if actor:
            section.deleted_by = str(actor.id)
        await self.db.flush()

        await record_audit_log(
            self.db, user=actor, action=AuditAction.DELETE.value,
            entity_type="Section", entity_id=section_id,
            changes={"before": {"deleted_at": None}, "after": {"deleted_at": section.deleted_at.isoformat()}},
            request=request,
        )
        await self.db.commit()

    # Academic Year Services
    async def create_academic_year(self, data: AcademicYearCreate, creator_id: str) -> AcademicYearResponse:
        ay = AcademicYear(
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            is_current=data.is_current,
            created_by=creator_id,
        )
        await self.repo.create_academic_year(ay)
        await self.db.commit()
        return AcademicYearResponse.model_validate(ay)

    async def list_academic_years(self) -> List[AcademicYearResponse]:
        ays = await self.repo.list_academic_years()
        return [AcademicYearResponse.model_validate(a) for a in ays]

    async def update_academic_year(
        self, academic_year_id: str, data: AcademicYearUpdate, actor: Optional[User] = None, request: Optional[Request] = None
    ) -> AcademicYearResponse:
        ay = await self.repo.get_academic_year_by_id(academic_year_id)
        if not ay:
            raise NotFoundError("Academic year not found")

        updates = data.model_dump(exclude_unset=True)
        before: dict = {}
        after: dict = {}

        if "name" in updates and updates["name"] != ay.name:
            existing = await self.repo.get_academic_year_by_name(updates["name"], exclude_id=academic_year_id)
            if existing:
                raise ConflictError(f"Academic year '{updates['name']}' already exists")
            before["name"], after["name"] = ay.name, updates["name"]
            ay.name = updates["name"]

        start_date = updates.get("start_date", ay.start_date)
        end_date = updates.get("end_date", ay.end_date)
        if end_date <= start_date:
            raise ValidationError("End date must be after start date")

        if "start_date" in updates and updates["start_date"] != ay.start_date:
            before["start_date"], after["start_date"] = str(ay.start_date), str(updates["start_date"])
            ay.start_date = updates["start_date"]
        if "end_date" in updates and updates["end_date"] != ay.end_date:
            before["end_date"], after["end_date"] = str(ay.end_date), str(updates["end_date"])
            ay.end_date = updates["end_date"]
        if "is_current" in updates and updates["is_current"] != ay.is_current:
            before["is_current"], after["is_current"] = ay.is_current, updates["is_current"]
            ay.is_current = updates["is_current"]

        if after:
            try:
                await self.db.flush()
            except IntegrityError as exc:
                await self.db.rollback()
                raise ConflictError("Could not update academic year — a conflicting record already exists.") from exc

            await record_audit_log(
                self.db, user=actor, action=AuditAction.UPDATE.value,
                entity_type="AcademicYear", entity_id=academic_year_id,
                changes={"before": before, "after": after}, request=request,
            )
            await self.db.commit()

        return AcademicYearResponse.model_validate(ay)

    # Semester — fixed institutional catalog (1-1 .. 4-2), seeded once; no create/update API.
    async def list_semesters(self) -> List[SemesterResponse]:
        sems = await self.repo.list_semesters()
        return [SemesterResponse.model_validate(s) for s in sems]

    # Subject Services
    async def create_subject(self, data: SubjectCreate, creator_id: str) -> SubjectResponse:
        subject = Subject(
            department_id=data.department_id,
            code=data.code.upper(),
            name=data.name,
            credits=data.credits,
            max_mid_marks=data.max_mid_marks,
            max_internal_marks=data.max_internal_marks,
            max_external_marks=data.max_external_marks,
            created_by=creator_id,
        )
        await self.repo.create_subject(subject)
        await self.db.commit()
        return SubjectResponse.model_validate(subject)

    async def list_subjects(self, department_id: Optional[str] = None) -> List[SubjectResponse]:
        subs = await self.repo.list_subjects(department_id)
        return [SubjectResponse.model_validate(s) for s in subs]

    async def update_subject(
        self, subject_id: str, data: SubjectUpdate, actor: Optional[User] = None, request: Optional[Request] = None
    ) -> SubjectResponse:
        subject = await self.repo.get_subject_by_id(subject_id)
        if not subject:
            raise NotFoundError("Subject not found")

        updates = data.model_dump(exclude_unset=True)
        before: dict = {}
        after: dict = {}

        if "department_id" in updates and updates["department_id"] != str(subject.department_id):
            dept = await self.repo.get_department_by_id(updates["department_id"])
            if not dept:
                raise ValidationError(f"Department '{updates['department_id']}' not found")
            before["department_id"], after["department_id"] = str(subject.department_id), updates["department_id"]
            subject.department_id = updates["department_id"]
        if "code" in updates:
            new_code = updates["code"].upper()
            if new_code != subject.code:
                existing = await self.repo.get_subject_by_code(new_code, exclude_id=subject_id)
                if existing:
                    raise ConflictError(f"Subject code '{new_code}' already exists")
                before["code"], after["code"] = subject.code, new_code
                subject.code = new_code
        if "name" in updates and updates["name"] != subject.name:
            before["name"], after["name"] = subject.name, updates["name"]
            subject.name = updates["name"]
        if "credits" in updates and updates["credits"] != subject.credits:
            before["credits"], after["credits"] = subject.credits, updates["credits"]
            subject.credits = updates["credits"]
        if "max_mid_marks" in updates and updates["max_mid_marks"] != subject.max_mid_marks:
            before["max_mid_marks"], after["max_mid_marks"] = subject.max_mid_marks, updates["max_mid_marks"]
            subject.max_mid_marks = updates["max_mid_marks"]
        if "max_internal_marks" in updates and updates["max_internal_marks"] != subject.max_internal_marks:
            before["max_internal_marks"], after["max_internal_marks"] = subject.max_internal_marks, updates["max_internal_marks"]
            subject.max_internal_marks = updates["max_internal_marks"]
        if "max_external_marks" in updates and updates["max_external_marks"] != subject.max_external_marks:
            before["max_external_marks"], after["max_external_marks"] = subject.max_external_marks, updates["max_external_marks"]
            subject.max_external_marks = updates["max_external_marks"]

        if after:
            try:
                await self.db.flush()
            except IntegrityError as exc:
                await self.db.rollback()
                raise ConflictError("Could not update subject — a conflicting or invalid reference was found.") from exc

            await record_audit_log(
                self.db, user=actor, action=AuditAction.UPDATE.value,
                entity_type="Subject", entity_id=subject_id,
                changes={"before": before, "after": after}, request=request,
            )
            await self.db.commit()

        return SubjectResponse.model_validate(subject)

    # --- User Admin Services --------------------------------------------
    def _profile(self, user: User) -> UserProfileResponse:
        return AuthService(self.db).get_current_user_profile(user)

    async def _provision_student_record(self, user: User, details: StudentProvisionDetails, department_id: str, creator_id: str) -> None:
        section = await self.repo.get_section_by_id(details.section_id)
        if not section:
            raise ValidationError(f"Section '{details.section_id}' not found")
        semester = await self.repo.get_semester_by_id(details.semester_id)
        if not semester:
            raise ValidationError(f"Semester '{details.semester_id}' not found")

        student = Student(
            user_id=user.id,
            roll_number=details.roll_number.upper(),
            registration_number=details.registration_number.upper(),
            date_of_birth=details.date_of_birth,
            batch_year=details.batch_year,
            department_id=department_id,
            current_semester_id=semester.id,
            created_by=creator_id,
        )
        await self.student_repo.create_student(student)
        await self.db.flush()

        from app.features.students.models import StudentEnrollment
        enrollment = StudentEnrollment(student_id=student.id, section_id=section.id, semester_id=semester.id)
        self.db.add(enrollment)

    async def create_user_by_admin(
        self, data: UserCreateRequest, creator_id: str, actor: Optional[User] = None, request: Optional[Request] = None
    ) -> AdminCreateUserResponse:
        role_entity = await self.auth_repo.get_role_by_name(data.role)
        if not role_entity:
            raise ValidationError(f"Unknown role '{data.role}'")

        existing = await self.auth_repo.get_user_by_email(data.email)
        if existing:
            raise ConflictError(f"User with email '{data.email}' already exists")

        if data.password:
            temporary_password = data.password
        elif role_entity.name == "STUDENT" and data.student_details:
            temporary_password = generate_student_default_password(data.student_details.roll_number)
        else:
            temporary_password = generate_temporary_password()

        user = User(
            email=data.email.lower(),
            hashed_password=get_password_hash(temporary_password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            department_id=data.department_id,
            force_password_change=True,
            created_by=creator_id,
        )
        user.roles.append(role_entity)
        await self.auth_repo.create_user(user)
        await self.db.flush()

        if role_entity.name == "STUDENT":
            await self._provision_student_record(user, data.student_details, data.department_id, creator_id)

        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError(
                "Could not create user — the email, roll number, or registration number is already in use."
            ) from exc

        email_sent = await asyncio.to_thread(
            send_email,
            user.email,
            "Your SCMS account has been created",
            (
                f"Hello {user.first_name},\n\n"
                f"An account has been created for you on the Student Counselling Management System.\n"
                f"Email: {user.email}\nTemporary password: {temporary_password}\n\n"
                f"You will be required to set a new password on first login."
            ),
        )

        refreshed = await self.auth_repo.get_user_by_id(str(user.id))

        await record_audit_log(
            self.db, user=actor, action=AuditAction.CREATE.value,
            entity_type="User", entity_id=str(user.id),
            changes={"email": user.email, "role": role_entity.name}, request=request,
        )
        await self.db.commit()

        return AdminCreateUserResponse(
            user=self._profile(refreshed), temporary_password=temporary_password, email_sent=email_sent
        )

    async def list_users(
        self,
        role: Optional[str],
        department_id: Optional[str],
        is_active: Optional[bool],
        search: Optional[str],
        params: PaginationParams,
    ) -> PaginatedResponse[UserListItemResponse]:
        users, total = await self.auth_repo.list_users(
            role=role, department_id=department_id, is_active=is_active, search=search,
            offset=params.offset, limit=params.per_page,
        )
        items = [
            UserListItemResponse(
                id=str(u.id),
                email=u.email,
                username=u.username,
                full_name=u.full_name,
                roles=[r.name for r in u.roles],
                department_id=str(u.department_id) if u.department_id else None,
                is_active=u.is_active,
                force_password_change=u.force_password_change,
                last_login_at=u.last_login_at,
                created_at=u.created_at,
            )
            for u in users
        ]
        return PaginatedResponse.create(items, total, params)

    async def get_user(self, user_id: str) -> UserProfileResponse:
        user = await self.auth_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return self._profile(user)

    async def update_user(self, user_id: str, data: UserUpdateRequest) -> UserProfileResponse:
        user = await self.auth_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        if data.first_name is not None:
            user.first_name = data.first_name
        if data.last_name is not None:
            user.last_name = data.last_name
        if data.phone is not None:
            user.phone = data.phone
        if data.department_id is not None:
            user.department_id = data.department_id
        if data.role is not None:
            role_entity = await self.auth_repo.get_role_by_name(data.role)
            if not role_entity:
                raise ValidationError(f"Unknown role '{data.role}'")
            user.roles = [role_entity]

        await self.db.commit()
        refreshed = await self.auth_repo.get_user_by_id(user_id)
        return self._profile(refreshed)

    async def deactivate_user(self, user_id: str, actor: Optional[User] = None, request: Optional[Request] = None) -> None:
        user = await self.auth_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        await self.auth_repo.set_active(user, False)
        await self.auth_repo.revoke_all_user_tokens(user_id)
        await record_audit_log(
            self.db, user=actor, action=AuditAction.UPDATE.value,
            entity_type="User", entity_id=user_id, changes={"is_active": False}, request=request,
        )
        await self.db.commit()

    async def activate_user(self, user_id: str, actor: Optional[User] = None, request: Optional[Request] = None) -> None:
        user = await self.auth_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        await self.auth_repo.set_active(user, True)
        await record_audit_log(
            self.db, user=actor, action=AuditAction.UPDATE.value,
            entity_type="User", entity_id=user_id, changes={"is_active": True}, request=request,
        )
        await self.db.commit()

    async def admin_reset_password(
        self, user_id: str, actor: Optional[User] = None, request: Optional[Request] = None
    ) -> AdminResetPasswordResponse:
        user = await self.auth_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        temporary_password = generate_temporary_password()
        await self.auth_repo.update_password(user, get_password_hash(temporary_password), force_password_change=True)
        await self.auth_repo.revoke_all_user_tokens(user_id)
        await record_audit_log(
            self.db, user=actor, action=AuditAction.PASSWORD_RESET.value,
            entity_type="User", entity_id=user_id, request=request,
        )
        await self.db.commit()

        email_sent = await asyncio.to_thread(
            send_email,
            user.email,
            "Your SCMS password has been reset",
            (
                f"Hello {user.first_name},\n\nYour password was reset by an administrator.\n"
                f"Temporary password: {temporary_password}\n\nYou will be required to set a new password on next login."
            ),
        )
        return AdminResetPasswordResponse(temporary_password=temporary_password, email_sent=email_sent)

    async def list_user_sessions(self, user_id: str) -> List[SessionResponse]:
        user = await self.auth_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        sessions = await self.auth_repo.list_active_sessions(user_id)
        return [
            SessionResponse(
                id=str(s.id), created_at=s.created_at, expires_at=s.expires_at,
                remember_me=s.remember_me, user_agent=s.user_agent, ip_address=s.ip_address,
                is_current=False,
            )
            for s in sessions
        ]

    async def force_logout_user(self, user_id: str) -> None:
        user = await self.auth_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        await self.auth_repo.revoke_all_user_tokens(user_id)
        await self.db.commit()

    async def assign_counsellor(self, data: AssignCounsellorRequest) -> None:
        student = await self.student_repo.get_student_by_id(data.student_id)
        if not student:
            raise NotFoundError("Student not found")

        counsellor = await self.auth_repo.get_user_by_id(data.counsellor_id)
        if not counsellor or "COUNSELLOR" not in {r.name for r in counsellor.roles}:
            raise ValidationError("Selected user is not an active Counsellor")

        semester = await self.repo.get_semester_by_id(data.semester_id)
        if not semester:
            raise ValidationError(f"Semester '{data.semester_id}' not found")

        await self.repo.close_open_counsellor_assignments(data.student_id)
        assignment = CounsellorAssignment(
            student_id=data.student_id,
            counsellor_id=data.counsellor_id,
            semester_id=data.semester_id,
            effective_from=datetime.now(timezone.utc),
        )
        await self.repo.create_counsellor_assignment(assignment)
        await self.db.commit()

    # Bulk provisioning lives in app/features/imports — the Office Import
    # module. It replaced the UUID-and-CSV-template importer that used to sit
    # here: an office does not hold section or semester identifiers, so a
    # template demanding them could never be filled in without an operator
    # translating the real list by hand first.
