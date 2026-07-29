from collections import defaultdict
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ValidationError
from app.core.events import event_bus, DomainEvent
from app.features.academics.models import Mark, SGPAHistory, Backlog
from app.features.academics.repository import AcademicsRepository
from app.features.academics.schemas import (
    BulkMarksCreate,
    MarksResponse,
    SGPACalculationResponse,
    BacklogResponse,
    StudentAcademicRecordResponse,
    SemesterResultBlock,
    SubjectResultRow,
)
from app.features.admin.repository import AdminRepository
from app.core.enums import TimelineEventType, BacklogStatus

# A subject is considered passed once its combined percentage across all
# recorded assessments reaches this threshold — matches the existing
# EXTERNAL-marks backlog-flagging threshold used below for consistency.
PASS_THRESHOLD = 0.40

# Letter grades for display only — SGPA/CGPA are computed from the raw
# percentage (see calculate_sgpa), never from these bands, so widening a band
# here cannot change a student's GPA.
_GRADE_BANDS = [(90, "O"), (80, "A"), (70, "B"), (60, "C"), (50, "D"), (40, "E")]


def _letter_grade(percentage: Optional[float]) -> Optional[str]:
    if percentage is None:
        return None
    for floor, letter in _GRADE_BANDS:
        if percentage >= floor:
            return letter
    return "F"


def _mark_to_response(mark: Mark) -> MarksResponse:
    return MarksResponse(
        id=str(mark.id),
        student_id=str(mark.student_id),
        subject_id=str(mark.subject_id),
        semester_id=str(mark.semester_id),
        assessment_type=mark.assessment_type,
        marks_obtained=mark.marks_obtained,
        max_marks=mark.max_marks,
        recorded_by=str(mark.recorded_by_user_id),
        created_at=mark.created_at,
    )


class AcademicsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AcademicsRepository(db)
        self.admin_repo = AdminRepository(db)

    async def record_bulk_marks(
        self, data: BulkMarksCreate, faculty_id: str
    ) -> List[MarksResponse]:
        created_list = []
        for item in data.records:
            if item.marks_obtained > item.max_marks:
                raise ValidationError(f"Marks obtained ({item.marks_obtained}) cannot exceed max marks ({item.max_marks}).")

            mark = Mark(
                student_id=item.student_id,
                subject_id=data.subject_id,
                semester_id=data.semester_id,
                assessment_type=data.assessment_type.upper(),
                marks_obtained=item.marks_obtained,
                max_marks=item.max_marks,
                recorded_by_user_id=faculty_id,
            )
            created = await self.repo.upsert_mark(mark)
            await self.db.flush()
            created_list.append(created)

            # Auto-flag backlog if external grade < pass threshold
            if data.assessment_type.upper() == "EXTERNAL" and (item.marks_obtained / item.max_marks) < PASS_THRESHOLD:
                backlog = Backlog(
                    student_id=item.student_id,
                    subject_id=data.subject_id,
                    semester_id=data.semester_id,
                    status=BacklogStatus.ACTIVE.value,
                )
                await self.repo.create_backlog(backlog)

                await event_bus.publish(
                    DomainEvent(
                        type=TimelineEventType.BACKLOG_ADDED.value,
                        student_id=item.student_id,
                        actor_id=faculty_id,
                        metadata={"subject_id": data.subject_id},
                    )
                )

        await self.db.commit()

        await event_bus.publish(
            DomainEvent(
                type=TimelineEventType.MARKS_UPDATED.value,
                actor_id=faculty_id,
                metadata={"subject_id": data.subject_id, "assessment_type": data.assessment_type},
            )
        )

        return [_mark_to_response(m) for m in created_list]

    async def calculate_sgpa(self, student_id: str, semester_id: str) -> SGPACalculationResponse:
        marks = await self.repo.get_student_marks(student_id, semester_id)
        if not marks:
            raise ValidationError("No marks have been recorded for this student in the selected semester yet")

        by_subject: dict = defaultdict(list)
        for m in marks:
            by_subject[str(m.subject_id)].append(m)

        subjects = await self.admin_repo.get_subjects_by_ids(list(by_subject.keys()))
        subjects_by_id = {str(s.id): s for s in subjects}

        weighted_points = 0.0
        total_credits = 0
        earned_credits = 0
        for subject_id, subject_marks in by_subject.items():
            obtained = sum(m.marks_obtained for m in subject_marks)
            maximum = sum(m.max_marks for m in subject_marks)
            subject_percentage = (obtained / maximum) if maximum else 0.0
            grade_points = round(subject_percentage * 10, 2)

            subject = subjects_by_id.get(subject_id)
            credits = subject.credits if subject else 0

            weighted_points += grade_points * credits
            total_credits += credits
            if subject_percentage >= PASS_THRESHOLD:
                earned_credits += credits

        sgpa_val = round(weighted_points / total_credits, 2) if total_credits else 0.0

        # Cumulative GPA: credit-weighted average across every semester on
        # record, including the one just computed (upserted below).
        history = await self.repo.get_student_sgpa_history(student_id)
        other_semesters = [h for h in history if str(h.semester_id) != semester_id]
        cumulative_points = sum(h.sgpa * h.total_credits for h in other_semesters) + (sgpa_val * total_credits)
        cumulative_credits = sum(h.total_credits for h in other_semesters) + total_credits
        cgpa_val = round(cumulative_points / cumulative_credits, 2) if cumulative_credits else sgpa_val

        entry = SGPAHistory(
            student_id=student_id,
            semester_id=semester_id,
            sgpa=sgpa_val,
            cgpa=cgpa_val,
            total_credits=total_credits,
        )
        await self.repo.save_sgpa_history(entry)
        await self.db.commit()

        await event_bus.publish(
            DomainEvent(
                type=TimelineEventType.SGPA_CALCULATED.value,
                student_id=student_id,
                metadata={"semester_id": semester_id, "sgpa": sgpa_val, "cgpa": cgpa_val},
            )
        )

        return SGPACalculationResponse(
            student_id=student_id,
            semester_id=semester_id,
            sgpa=sgpa_val,
            cgpa=cgpa_val,
            total_credits=total_credits,
            earned_credits=earned_credits,
        )

    async def get_student_academic_record(self, student_id: str) -> StudentAcademicRecordResponse:
        """Semester-wise transcript for the Academics tab. Marks are read-only
        here — they originate from faculty entry and admin imports, never from
        the student."""
        rows = await self.repo.get_student_marks_detailed(student_id)
        history = await self.repo.get_student_sgpa_history(student_id)
        backlogs = await self.repo.get_student_backlogs(student_id)

        sgpa_by_semester = {str(h.semester_id): h for h in history}
        backlogs_by_semester: dict[str, int] = defaultdict(int)
        for b in backlogs:
            if b.status == BacklogStatus.ACTIVE.value:
                backlogs_by_semester[str(b.semester_id)] += 1

        # semester -> subject -> assessment rows
        semesters: dict[str, dict] = {}
        for r in rows:
            sem_key = str(r.semester_id)
            sem = semesters.setdefault(
                sem_key,
                {"name": r.semester_name, "number": r.semester_number, "subjects": {}},
            )
            subj = sem["subjects"].setdefault(
                str(r.subject_id),
                {
                    "code": r.subject_code,
                    "name": r.subject_name,
                    "credits": r.credits,
                    "marks": {},
                },
            )
            subj["marks"][r.assessment_type.upper()] = (r.marks_obtained, r.max_marks)

        blocks: List[SemesterResultBlock] = []
        for sem_key, sem in sorted(semesters.items(), key=lambda kv: kv[1]["number"]):
            subject_rows: List[SubjectResultRow] = []
            for subject_id, subj in sorted(sem["subjects"].items(), key=lambda kv: kv[1]["code"]):
                marks = subj["marks"]
                obtained = sum(v[0] for v in marks.values())
                maximum = sum(v[1] for v in marks.values())
                percentage = round((obtained / maximum) * 100, 1) if maximum else None
                has_external = "EXTERNAL" in marks

                subject_rows.append(
                    SubjectResultRow(
                        subject_id=subject_id,
                        subject_code=subj["code"],
                        subject_name=subj["name"],
                        credits=subj["credits"],
                        mid_1=marks.get("MID_TERM_1", (None, None))[0],
                        mid_2=marks.get("MID_TERM_2", (None, None))[0],
                        internal=marks.get("INTERNAL", (None, None))[0],
                        external=marks.get("EXTERNAL", (None, None))[0],
                        total_obtained=obtained if marks else None,
                        total_max=maximum if marks else None,
                        percentage=percentage,
                        grade=_letter_grade(percentage),
                        result=(
                            "IN_PROGRESS"
                            if not has_external or percentage is None
                            else ("PASS" if percentage >= PASS_THRESHOLD * 100 else "FAIL")
                        ),
                    )
                )

            entry = sgpa_by_semester.get(sem_key)
            blocks.append(
                SemesterResultBlock(
                    semester_id=sem_key,
                    semester_name=sem["name"],
                    semester_number=sem["number"],
                    subjects=subject_rows,
                    sgpa=entry.sgpa if entry else None,
                    cgpa=entry.cgpa if entry else None,
                    total_credits=entry.total_credits if entry else None,
                    active_backlogs=backlogs_by_semester.get(sem_key, 0),
                )
            )

        latest = history[-1] if history else None
        return StudentAcademicRecordResponse(
            student_id=student_id,
            cgpa=latest.cgpa if latest else None,
            latest_sgpa=latest.sgpa if latest else None,
            total_active_backlogs=sum(backlogs_by_semester.values()),
            semesters=blocks,
        )

    async def get_student_backlogs(self, student_id: str) -> List[BacklogResponse]:
        backlogs = await self.repo.get_student_backlogs(student_id)
        subjects = await self.admin_repo.get_subjects_by_ids([str(b.subject_id) for b in backlogs])
        subjects_by_id = {str(s.id): s for s in subjects}

        results = []
        for b in backlogs:
            subject = subjects_by_id.get(str(b.subject_id))
            results.append(
                BacklogResponse(
                    id=str(b.id),
                    student_id=str(b.student_id),
                    subject_id=str(b.subject_id),
                    subject_code=subject.code if subject else None,
                    subject_name=subject.name if subject else None,
                    semester_id=str(b.semester_id),
                    status=b.status,
                    cleared_at_semester_id=str(b.cleared_at_semester_id) if b.cleared_at_semester_id else None,
                    cleared_date=b.cleared_date,
                    created_at=b.created_at,
                )
            )
        return results
