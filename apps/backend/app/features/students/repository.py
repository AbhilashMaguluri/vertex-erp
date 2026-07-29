from typing import List, Optional, Tuple
from sqlalchemy import Integer, Numeric, case, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload
from app.features.students.models import Student, StudentEnrollment, CounsellorAssignment
from app.features.auth.models import User
from app.features.admin.models import Department, Section, Semester
from app.features.academics.models import Backlog, SGPAHistory
from app.features.attendance.models import AttendanceRecord
from app.features.counselling.models import CounsellingSession

# Which attendance states count as "attended" when computing a percentage.
# Kept identical to StudentService.get_student_360_workspace so the caseload
# table and the 360 workspace never disagree about the same student's number.
PRESENT_STATUSES = ("PRESENT", "ON_DUTY")

CASELOAD_SORT_FIELDS = (
    "roll_number", "name", "attendance", "cgpa", "risk", "last_session",
)

# Risk ordered by severity so `sort_by=risk` surfaces the students who need
# attention first rather than sorting the enum alphabetically.
_RISK_SEVERITY = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "NONE": 1}


class StudentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_student_by_id(self, student_id: str) -> Optional[Student]:
        query = (
            select(Student)
            .where(Student.id == student_id, Student.deleted_at.is_(None))
            .options(
                selectinload(Student.user),
                selectinload(Student.profile),
                selectinload(Student.counsellor_assignments).selectinload(CounsellorAssignment.counsellor),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_student_by_user_id(self, user_id: str) -> Optional[Student]:
        query = (
            select(Student)
            .where(Student.user_id == user_id, Student.deleted_at.is_(None))
            .options(
                selectinload(Student.user),
                selectinload(Student.profile),
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

    async def search_students(self, query: str, limit: int = 8) -> List[Student]:
        like = f"%{query.lower()}%"
        q = (
            select(Student)
            .join(User, Student.user_id == User.id)
            .where(
                Student.deleted_at.is_(None),
                or_(
                    func.lower(Student.roll_number).like(like),
                    func.lower(User.first_name + " " + User.last_name).like(like),
                ),
            )
            .options(
                selectinload(Student.user),
                selectinload(Student.counsellor_assignments),
            )
            .order_by(Student.roll_number)
            .limit(limit)
        )
        res = await self.db.execute(q)
        return list(res.scalars().all())

    # ------------------------------------------------------------------
    # Caseload
    #
    # One query per page — every per-student number (attendance %, CGPA,
    # backlog count, last counselling date) is a pre-aggregated subquery
    # joined onto the roster rather than an N+1 loop over students. This is
    # what lets the counsellor's primary page stay responsive on a caseload
    # of hundreds and an institution of thousands.
    # ------------------------------------------------------------------

    @staticmethod
    def _attendance_subq():
        return (
            select(
                AttendanceRecord.student_id.label("student_id"),
                func.count(AttendanceRecord.id).label("total_classes"),
                func.sum(
                    case((AttendanceRecord.status.in_(PRESENT_STATUSES), 1), else_=0)
                ).label("attended_classes"),
            )
            .group_by(AttendanceRecord.student_id)
            .subquery()
        )

    @staticmethod
    def _latest_gpa_subq():
        """Most recent SGPA/CGPA row per student (ordered by insertion, matching
        AcademicsRepository.get_student_sgpa_history which reads created_at asc)."""
        ranked = (
            select(
                SGPAHistory.student_id.label("student_id"),
                SGPAHistory.sgpa.label("sgpa"),
                SGPAHistory.cgpa.label("cgpa"),
                func.row_number()
                .over(
                    partition_by=SGPAHistory.student_id,
                    order_by=SGPAHistory.created_at.desc(),
                )
                .label("rn"),
            )
            .subquery()
        )
        return (
            select(ranked.c.student_id, ranked.c.sgpa, ranked.c.cgpa)
            .where(ranked.c.rn == 1)
            .subquery()
        )

    @staticmethod
    def _backlog_subq():
        return (
            select(
                Backlog.student_id.label("student_id"),
                func.count(Backlog.id).label("active_backlogs"),
            )
            .where(Backlog.status == "ACTIVE")
            .group_by(Backlog.student_id)
            .subquery()
        )

    @staticmethod
    def _session_subq():
        return (
            select(
                CounsellingSession.student_id.label("student_id"),
                func.max(CounsellingSession.session_date).label("last_session_date"),
                func.count(CounsellingSession.id).label("session_count"),
            )
            .group_by(CounsellingSession.student_id)
            .subquery()
        )

    @staticmethod
    def _current_enrollment_subq():
        """The student's furthest-progressed enrollment — highest semester
        number wins, which is what "current section/semester" means for a
        student who has rows for every semester they've been through."""
        ranked = (
            select(
                StudentEnrollment.student_id.label("student_id"),
                StudentEnrollment.section_id.label("section_id"),
                StudentEnrollment.semester_id.label("semester_id"),
                Semester.number.label("semester_number"),
                Semester.name.label("semester_name"),
                func.row_number()
                .over(
                    partition_by=StudentEnrollment.student_id,
                    order_by=Semester.number.desc(),
                )
                .label("rn"),
            )
            .join(Semester, Semester.id == StudentEnrollment.semester_id)
            .subquery()
        )
        return (
            select(
                ranked.c.student_id,
                ranked.c.section_id,
                ranked.c.semester_id,
                ranked.c.semester_number,
                ranked.c.semester_name,
            )
            .where(ranked.c.rn == 1)
            .subquery()
        )

    async def list_caseload(
        self,
        counsellor_id: Optional[str] = None,
        search: Optional[str] = None,
        year: Optional[int] = None,
        section_id: Optional[str] = None,
        semester_id: Optional[str] = None,
        department_id: Optional[str] = None,
        batch_year: Optional[int] = None,
        risk_level: Optional[str] = None,
        status: Optional[str] = None,
        min_attendance: Optional[float] = None,
        max_attendance: Optional[float] = None,
        min_cgpa: Optional[float] = None,
        max_cgpa: Optional[float] = None,
        has_backlogs: Optional[bool] = None,
        sort_by: str = "roll_number",
        sort_dir: str = "asc",
        page: int = 1,
        per_page: int = 25,
    ) -> Tuple[List[dict], int]:
        """Returns (rows, total). Each row is a plain dict of the columns the
        caseload table renders — deliberately not ORM entities, so paging
        through a large caseload doesn't hydrate a graph of related objects."""
        att = self._attendance_subq()
        gpa = self._latest_gpa_subq()
        bk = self._backlog_subq()
        cs = self._session_subq()
        enr = self._current_enrollment_subq()

        counsellor = aliased(User)

        attendance_pct = case(
            (
                func.coalesce(att.c.total_classes, 0) > 0,
                func.round(
                    cast(att.c.attended_classes, Numeric) * 100 / cast(att.c.total_classes, Numeric),
                    1,
                ),
            ),
            else_=None,
        )

        # Section.year is authoritative when set; otherwise derive the study
        # year from the semester number (1-1/1-2 -> 1, ... 4-1/4-2 -> 4).
        # cast: SQLAlchemy types `/` as Numeric, so without this the study year
        # comes back as Decimal('4') instead of 4. Postgres has already floored
        # the integer division, so the cast is lossless.
        study_year = cast(
            func.coalesce(Section.year, (enr.c.semester_number + 1) / 2), Integer
        )

        def apply_joins(stmt):
            stmt = (
                stmt.select_from(Student)
                .join(User, User.id == Student.user_id)
                .outerjoin(enr, enr.c.student_id == Student.id)
                .outerjoin(Section, Section.id == enr.c.section_id)
                .outerjoin(Department, Department.id == Student.department_id)
                .outerjoin(att, att.c.student_id == Student.id)
                .outerjoin(gpa, gpa.c.student_id == Student.id)
                .outerjoin(bk, bk.c.student_id == Student.id)
                .outerjoin(cs, cs.c.student_id == Student.id)
                .outerjoin(
                    CounsellorAssignment,
                    (CounsellorAssignment.student_id == Student.id)
                    & (CounsellorAssignment.effective_to.is_(None)),
                )
                .outerjoin(counsellor, counsellor.id == CounsellorAssignment.counsellor_id)
            )
            return stmt

        filters = [Student.deleted_at.is_(None)]

        if counsellor_id:
            filters.append(CounsellorAssignment.counsellor_id == counsellor_id)
        if department_id:
            filters.append(Student.department_id == department_id)
        if batch_year:
            filters.append(Student.batch_year == batch_year)
        if risk_level:
            filters.append(Student.risk_level == risk_level.upper())
        if status:
            filters.append(Student.status == status.upper())
        if section_id:
            filters.append(enr.c.section_id == section_id)
        if semester_id:
            filters.append(enr.c.semester_id == semester_id)
        if year:
            filters.append(study_year == year)
        if min_attendance is not None:
            filters.append(attendance_pct >= min_attendance)
        if max_attendance is not None:
            filters.append(attendance_pct <= max_attendance)
        if min_cgpa is not None:
            filters.append(gpa.c.cgpa >= min_cgpa)
        if max_cgpa is not None:
            filters.append(gpa.c.cgpa <= max_cgpa)
        if has_backlogs is True:
            filters.append(func.coalesce(bk.c.active_backlogs, 0) > 0)
        elif has_backlogs is False:
            filters.append(func.coalesce(bk.c.active_backlogs, 0) == 0)

        if search:
            # One box, every identifier a counsellor might have to hand: the
            # roll/reg number off a form, a name, a phone number from a parent
            # call, an email, or the branch/section they're scanning through.
            like = f"%{search.lower()}%"
            filters.append(
                or_(
                    func.lower(Student.roll_number).like(like),
                    func.lower(Student.registration_number).like(like),
                    func.lower(User.first_name + " " + User.last_name).like(like),
                    func.lower(User.email).like(like),
                    func.lower(func.coalesce(User.phone, "")).like(like),
                    func.lower(func.coalesce(Department.name, "")).like(like),
                    func.lower(func.coalesce(Department.code, "")).like(like),
                    func.lower(func.coalesce(Section.name, "")).like(like),
                )
            )

        risk_rank = case(
            *[(Student.risk_level == k, v) for k, v in _RISK_SEVERITY.items()],
            else_=0,
        )
        sort_targets = {
            "roll_number": Student.roll_number,
            "name": func.lower(User.first_name + " " + User.last_name),
            "attendance": attendance_pct,
            "cgpa": gpa.c.cgpa,
            "risk": risk_rank,
            "last_session": cs.c.last_session_date,
        }
        sort_col = sort_targets.get(sort_by, Student.roll_number)
        # NULLs (no attendance yet, never counselled) sort last in both
        # directions — an unknown value is not the same as a bad one.
        order = sort_col.desc().nullslast() if sort_dir == "desc" else sort_col.asc().nullslast()

        query = apply_joins(
            select(
                Student.id.label("id"),
                Student.roll_number,
                Student.registration_number,
                Student.risk_level,
                Student.status,
                Student.batch_year,
                Student.department_id,
                Student.gender,
                Student.photo_url,
                User.first_name,
                User.last_name,
                User.email,
                User.phone,
                Department.name.label("department_name"),
                Department.code.label("department_code"),
                Section.id.label("section_id"),
                Section.name.label("section_name"),
                study_year.label("study_year"),
                enr.c.semester_id.label("semester_id"),
                enr.c.semester_name.label("semester_name"),
                enr.c.semester_number.label("semester_number"),
                attendance_pct.label("attendance_percentage"),
                att.c.total_classes,
                att.c.attended_classes,
                gpa.c.sgpa,
                gpa.c.cgpa,
                func.coalesce(bk.c.active_backlogs, 0).label("active_backlogs"),
                cs.c.last_session_date,
                func.coalesce(cs.c.session_count, 0).label("session_count"),
                CounsellorAssignment.counsellor_id,
                counsellor.first_name.label("counsellor_first_name"),
                counsellor.last_name.label("counsellor_last_name"),
            )
        ).where(*filters)

        count_query = apply_joins(select(func.count(func.distinct(Student.id)))).where(*filters)

        query = (
            query.order_by(order, Student.roll_number.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )

        rows_res = await self.db.execute(query)
        count_res = await self.db.execute(count_query)

        return [dict(r._mapping) for r in rows_res.all()], count_res.scalar_one()

    async def caseload_facets(self, counsellor_id: Optional[str] = None) -> dict:
        """Distinct filter values that actually occur in this caseload."""
        enr = self._current_enrollment_subq()
        study_year = cast(
            func.coalesce(Section.year, (enr.c.semester_number + 1) / 2), Integer
        )

        query = (
            select(
                study_year.label("study_year"),
                Section.id.label("section_id"),
                Section.name.label("section_name"),
                enr.c.semester_id,
                enr.c.semester_name,
                Department.id.label("department_id"),
                Department.name.label("department_name"),
                Student.batch_year,
                Student.risk_level,
                Student.status,
            )
            .select_from(Student)
            .outerjoin(enr, enr.c.student_id == Student.id)
            .outerjoin(Section, Section.id == enr.c.section_id)
            .outerjoin(Department, Department.id == Student.department_id)
            .where(Student.deleted_at.is_(None))
            .distinct()
        )
        if counsellor_id:
            query = query.join(
                CounsellorAssignment,
                (CounsellorAssignment.student_id == Student.id)
                & (CounsellorAssignment.effective_to.is_(None))
                & (CounsellorAssignment.counsellor_id == counsellor_id),
            )

        res = await self.db.execute(query)
        rows = res.all()

        years, sections, semesters, batches, risks, statuses = set(), {}, {}, set(), set(), set()
        departments: dict[str, str] = {}
        for r in rows:
            if r.study_year is not None:
                years.add(int(r.study_year))
            if r.section_id:
                sections[str(r.section_id)] = r.section_name
            if r.semester_id:
                semesters[str(r.semester_id)] = r.semester_name
            if r.department_id:
                departments[str(r.department_id)] = r.department_name
            if r.batch_year:
                batches.add(r.batch_year)
            if r.risk_level:
                risks.add(r.risk_level)
            if r.status:
                statuses.add(r.status)

        return {
            "years": sorted(years),
            "sections": [{"id": k, "label": v} for k, v in sorted(sections.items(), key=lambda x: x[1] or "")],
            "semesters": [{"id": k, "label": v} for k, v in sorted(semesters.items(), key=lambda x: x[1] or "")],
            "departments": [{"id": k, "label": v} for k, v in sorted(departments.items(), key=lambda x: x[1] or "")],
            "batch_years": sorted(batches, reverse=True),
            "risk_levels": sorted(risks, key=lambda r: -_RISK_SEVERITY.get(r, 0)),
            "statuses": sorted(statuses),
        }

    async def caseload_aggregates(self, counsellor_id: Optional[str] = None) -> dict:
        """Cohort-level rollups for the counsellor dashboard: headcount, gender
        split, averages, and the three at-risk buckets — one scan, not one
        query per tile."""
        att = self._attendance_subq()
        gpa = self._latest_gpa_subq()
        bk = self._backlog_subq()
        enr = self._current_enrollment_subq()

        attendance_pct = case(
            (
                func.coalesce(att.c.total_classes, 0) > 0,
                cast(att.c.attended_classes, Numeric) * 100 / cast(att.c.total_classes, Numeric),
            ),
            else_=None,
        )
        study_year = cast(
            func.coalesce(Section.year, (enr.c.semester_number + 1) / 2), Integer
        )

        def base(*cols):
            stmt = (
                select(*cols)
                .select_from(Student)
                .outerjoin(enr, enr.c.student_id == Student.id)
                .outerjoin(Section, Section.id == enr.c.section_id)
                .outerjoin(att, att.c.student_id == Student.id)
                .outerjoin(gpa, gpa.c.student_id == Student.id)
                .outerjoin(bk, bk.c.student_id == Student.id)
                .where(Student.deleted_at.is_(None))
            )
            if counsellor_id:
                stmt = stmt.join(
                    CounsellorAssignment,
                    (CounsellorAssignment.student_id == Student.id)
                    & (CounsellorAssignment.effective_to.is_(None))
                    & (CounsellorAssignment.counsellor_id == counsellor_id),
                )
            return stmt

        totals = (
            await self.db.execute(
                base(
                    func.count(func.distinct(Student.id)).label("total"),
                    func.sum(case((Student.gender == "MALE", 1), else_=0)).label("male"),
                    func.sum(case((Student.gender == "FEMALE", 1), else_=0)).label("female"),
                    func.sum(case((Student.gender.is_(None), 1), else_=0)).label("gender_unknown"),
                    func.avg(attendance_pct).label("avg_attendance"),
                    func.avg(gpa.c.cgpa).label("avg_cgpa"),
                    func.sum(
                        case((Student.risk_level.in_(("HIGH", "CRITICAL")), 1), else_=0)
                    ).label("high_risk"),
                    func.sum(case((attendance_pct < 75, 1), else_=0)).label("below_attendance"),
                    func.sum(
                        case((func.coalesce(bk.c.active_backlogs, 0) > 0, 1), else_=0)
                    ).label("with_backlogs"),
                )
            )
        ).first()

        by_year = (
            await self.db.execute(
                base(study_year.label("bucket"), func.count(func.distinct(Student.id)).label("count"))
                .group_by(study_year)
                .order_by(study_year)
            )
        ).all()

        by_section = (
            await self.db.execute(
                base(Section.name.label("bucket"), func.count(func.distinct(Student.id)).label("count"))
                .group_by(Section.name)
                .order_by(Section.name)
            )
        ).all()

        by_risk = (
            await self.db.execute(
                base(Student.risk_level.label("bucket"), func.count(func.distinct(Student.id)).label("count"))
                .group_by(Student.risk_level)
            )
        ).all()

        # Attendance banded into the tiers a counsellor actually acts on.
        # Students with no attendance recorded at all fall out of every band
        # (attendance_pct is NULL) rather than being counted as 0% defaulters.
        attendance_band = case(
            (attendance_pct < 50, "Below 50%"),
            (attendance_pct < 65, "50–64%"),
            (attendance_pct < 75, "65–74%"),
            (attendance_pct < 85, "75–84%"),
            (attendance_pct >= 85, "85%+"),
            else_=None,
        )
        by_attendance_band = (
            await self.db.execute(
                base(attendance_band.label("bucket"), func.count(func.distinct(Student.id)).label("count"))
                .where(attendance_pct.is_not(None))
                .group_by(attendance_band)
            )
        ).all()
        _BAND_ORDER = ["Below 50%", "50–64%", "65–74%", "75–84%", "85%+"]

        return {
            "total_students": totals.total or 0,
            "male": int(totals.male or 0),
            "female": int(totals.female or 0),
            "gender_unknown": int(totals.gender_unknown or 0),
            "average_attendance": round(float(totals.avg_attendance), 1) if totals.avg_attendance is not None else None,
            "average_cgpa": round(float(totals.avg_cgpa), 2) if totals.avg_cgpa is not None else None,
            "high_risk_count": int(totals.high_risk or 0),
            "below_attendance_count": int(totals.below_attendance or 0),
            "with_backlogs_count": int(totals.with_backlogs or 0),
            "by_year": [{"bucket": str(b) if b is not None else "Unassigned", "count": c} for b, c in by_year],
            "by_section": [{"bucket": b or "Unassigned", "count": c} for b, c in by_section],
            "by_risk": [{"bucket": b, "count": c} for b, c in by_risk],
            "by_attendance_band": sorted(
                [{"bucket": b, "count": c} for b, c in by_attendance_band if b],
                key=lambda x: _BAND_ORDER.index(x["bucket"]),
            ),
        }

    async def get_caseload_row(self, student_id: str) -> Optional[dict]:
        """The same aggregated shape as one caseload row, for a single student.
        Used to prefill the session recorder and head the 360 workspace."""
        att = self._attendance_subq()
        gpa = self._latest_gpa_subq()
        bk = self._backlog_subq()
        cs = self._session_subq()
        enr = self._current_enrollment_subq()

        attendance_pct = case(
            (
                func.coalesce(att.c.total_classes, 0) > 0,
                func.round(
                    cast(att.c.attended_classes, Numeric) * 100 / cast(att.c.total_classes, Numeric),
                    1,
                ),
            ),
            else_=None,
        )
        # cast: SQLAlchemy types `/` as Numeric, so without this the study year
        # comes back as Decimal('4') instead of 4. Postgres has already floored
        # the integer division, so the cast is lossless.
        study_year = cast(
            func.coalesce(Section.year, (enr.c.semester_number + 1) / 2), Integer
        )

        query = (
            select(
                Student.id.label("id"),
                Student.roll_number,
                Student.registration_number,
                Student.risk_level,
                Student.status,
                Student.batch_year,
                Student.gender,
                Student.photo_url,
                User.first_name,
                User.last_name,
                User.email,
                Section.name.label("section_name"),
                study_year.label("study_year"),
                enr.c.semester_id.label("semester_id"),
                enr.c.semester_name.label("semester_name"),
                enr.c.semester_number.label("semester_number"),
                attendance_pct.label("attendance_percentage"),
                gpa.c.sgpa,
                gpa.c.cgpa,
                func.coalesce(bk.c.active_backlogs, 0).label("active_backlogs"),
                cs.c.last_session_date,
                func.coalesce(cs.c.session_count, 0).label("session_count"),
            )
            .select_from(Student)
            .join(User, User.id == Student.user_id)
            .outerjoin(enr, enr.c.student_id == Student.id)
            .outerjoin(Section, Section.id == enr.c.section_id)
            .outerjoin(att, att.c.student_id == Student.id)
            .outerjoin(gpa, gpa.c.student_id == Student.id)
            .outerjoin(bk, bk.c.student_id == Student.id)
            .outerjoin(cs, cs.c.student_id == Student.id)
            .where(Student.id == student_id, Student.deleted_at.is_(None))
        )
        res = await self.db.execute(query)
        row = res.first()
        return dict(row._mapping) if row else None

    async def list_roster(self, section_id: str, semester_id: str) -> List[Student]:
        query = (
            select(Student)
            .join(StudentEnrollment, StudentEnrollment.student_id == Student.id)
            .where(
                StudentEnrollment.section_id == section_id,
                StudentEnrollment.semester_id == semester_id,
                Student.deleted_at.is_(None),
            )
            .options(selectinload(Student.user))
            .order_by(Student.roll_number)
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    # ------------------------------------------------------------------
    # Academic Correction Requests
    # ------------------------------------------------------------------
    async def create_correction_request(
        self, request: "AcademicCorrectionRequest", log: "AcademicCorrectionLog"
    ) -> "AcademicCorrectionRequest":
        from app.features.students.models import AcademicCorrectionRequest, AcademicCorrectionLog
        self.db.add(request)
        self.db.add(log)
        await self.db.flush()
        return request

    async def get_correction_request_by_id(
        self, request_id: str
    ) -> Optional["AcademicCorrectionRequest"]:
        from app.features.students.models import AcademicCorrectionRequest, StudentDocument
        query = (
            select(AcademicCorrectionRequest)
            .where(AcademicCorrectionRequest.id == request_id)
            .options(
                selectinload(AcademicCorrectionRequest.student).selectinload(Student.user),
                selectinload(AcademicCorrectionRequest.counsellor),
                selectinload(AcademicCorrectionRequest.document),
                selectinload(AcademicCorrectionRequest.logs).selectinload(AcademicCorrectionLog.actor),
                selectinload(AcademicCorrectionRequest.logs).selectinload(AcademicCorrectionLog.document),
            )
        )
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def list_correction_requests_by_student(
        self, student_id: str
    ) -> List["AcademicCorrectionRequest"]:
        from app.features.students.models import AcademicCorrectionRequest, AcademicCorrectionLog
        query = (
            select(AcademicCorrectionRequest)
            .where(AcademicCorrectionRequest.student_id == student_id)
            .options(
                selectinload(AcademicCorrectionRequest.student).selectinload(Student.user),
                selectinload(AcademicCorrectionRequest.counsellor),
                selectinload(AcademicCorrectionRequest.document),
                selectinload(AcademicCorrectionRequest.logs).selectinload(AcademicCorrectionLog.actor),
                selectinload(AcademicCorrectionRequest.logs).selectinload(AcademicCorrectionLog.document),
            )
            .order_by(AcademicCorrectionRequest.created_at.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_correction_requests_by_counsellor(
        self, counsellor_id: Optional[str] = None
    ) -> List["AcademicCorrectionRequest"]:
        from app.features.students.models import AcademicCorrectionRequest, AcademicCorrectionLog
        query = (
            select(AcademicCorrectionRequest)
            .options(
                selectinload(AcademicCorrectionRequest.student).selectinload(Student.user),
                selectinload(AcademicCorrectionRequest.counsellor),
                selectinload(AcademicCorrectionRequest.document),
                selectinload(AcademicCorrectionRequest.logs).selectinload(AcademicCorrectionLog.actor),
                selectinload(AcademicCorrectionRequest.logs).selectinload(AcademicCorrectionLog.document),
            )
        )
        if counsellor_id:
            query = query.where(AcademicCorrectionRequest.counsellor_id == counsellor_id)

        query = query.order_by(AcademicCorrectionRequest.created_at.desc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def add_correction_log(self, log: "AcademicCorrectionLog") -> "AcademicCorrectionLog":
        self.db.add(log)
        await self.db.flush()
        return log

