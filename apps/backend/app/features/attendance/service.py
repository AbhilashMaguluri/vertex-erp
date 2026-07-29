import calendar
from collections import defaultdict
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError, ValidationError
from app.core.events import event_bus, DomainEvent
from app.features.attendance.models import AttendanceRecord, AttendanceCorrection
from app.features.attendance.repository import AttendanceRepository
from app.features.attendance.schemas import (
    BulkAttendanceCreate,
    AttendanceRecordResponse,
    MonthlyAttendancePoint,
    StudentAttendanceSummaryResponse,
    SubjectAttendanceSummary,
    CorrectionRequestCreate,
    CorrectionResponse,
)
from app.features.admin.repository import AdminRepository
from app.core.enums import TimelineEventType, ApprovalStatus


def _record_to_response(record: AttendanceRecord) -> AttendanceRecordResponse:
    return AttendanceRecordResponse(
        id=str(record.id),
        student_id=str(record.student_id),
        subject_id=str(record.subject_id),
        date=record.date,
        status=record.status,
        recorded_by=str(record.recorded_by_user_id),
        created_at=record.created_at,
    )


def _correction_to_response(correction: AttendanceCorrection, student_id: str) -> CorrectionResponse:
    return CorrectionResponse(
        id=str(correction.id),
        attendance_record_id=str(correction.attendance_record_id),
        student_id=student_id,
        requested_by=str(correction.requested_by_user_id),
        old_status=correction.old_status,
        new_status=correction.new_status,
        reason=correction.reason,
        approval_status=correction.status,
        reviewed_by=str(correction.reviewed_by_user_id) if correction.reviewed_by_user_id else None,
        created_at=correction.created_at,
    )


class AttendanceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AttendanceRepository(db)
        self.admin_repo = AdminRepository(db)

    async def record_bulk_attendance(
        self, data: BulkAttendanceCreate, faculty_id: str
    ) -> List[AttendanceRecordResponse]:
        created_records = []
        for rec in data.records:
            att = AttendanceRecord(
                student_id=rec.student_id,
                subject_id=data.subject_id,
                date=data.date,
                status=rec.status.upper(),
                recorded_by_user_id=faculty_id,
            )
            created = await self.repo.upsert_attendance_record(att)
            created_records.append(created)

        await self.db.commit()

        if data.records:
            await event_bus.publish(
                DomainEvent(
                    type=TimelineEventType.ATTENDANCE_UPDATED.value,
                    actor_id=faculty_id,
                    metadata={"subject_id": data.subject_id, "date": str(data.date), "count": len(data.records)},
                )
            )

        return [_record_to_response(r) for r in created_records]

    async def get_student_attendance_summary(self, student_id: str) -> StudentAttendanceSummaryResponse:
        records = await self.repo.get_student_attendance_records(student_id)

        if not records:
            # No percentage at all. Reporting 100% here would tell a newly
            # imported student they had perfect attendance in a semester that
            # has not been recorded yet.
            return StudentAttendanceSummaryResponse(
                student_id=student_id,
                overall_percentage=None,
                subject_summaries=[],
            )

        by_subject: dict = defaultdict(list)
        for r in records:
            by_subject[str(r.subject_id)].append(r)

        subjects = await self.admin_repo.get_subjects_by_ids(list(by_subject.keys()))
        subjects_by_id = {str(s.id): s for s in subjects}

        subject_summaries = []
        for subject_id, subject_records in by_subject.items():
            total = len(subject_records)
            attended = sum(1 for r in subject_records if r.status in ["PRESENT", "ON_DUTY"])
            subject = subjects_by_id.get(subject_id)
            subject_summaries.append(
                SubjectAttendanceSummary(
                    subject_id=subject_id,
                    subject_code=subject.code if subject else "UNKNOWN",
                    subject_name=subject.name if subject else "Unknown Subject",
                    total_classes=total,
                    attended_classes=attended,
                    percentage=round((attended / total) * 100, 1) if total else 0.0,
                )
            )
        subject_summaries.sort(key=lambda s: s.subject_code)

        total_classes = len(records)
        attended_classes = sum(1 for r in records if r.status in ["PRESENT", "ON_DUTY"])
        overall = round((attended_classes / total_classes) * 100, 1)

        return StudentAttendanceSummaryResponse(
            student_id=student_id,
            overall_percentage=overall,
            total_classes=total_classes,
            attended_classes=attended_classes,
            subject_summaries=subject_summaries,
            monthly_trend=self._monthly_trend(records),
        )

    @staticmethod
    def _monthly_trend(records) -> List[MonthlyAttendancePoint]:
        """Attendance grouped by calendar month, oldest first.

        Derived from the same records as the overall figure, so the trend and
        the headline percentage can never disagree."""
        by_month: dict = defaultdict(list)
        for r in records:
            by_month[(r.date.year, r.date.month)].append(r)

        points: List[MonthlyAttendancePoint] = []
        for (year, month) in sorted(by_month):
            month_records = by_month[(year, month)]
            total = len(month_records)
            attended = sum(1 for r in month_records if r.status in ["PRESENT", "ON_DUTY"])
            points.append(
                MonthlyAttendancePoint(
                    month=f"{year:04d}-{month:02d}",
                    label=f"{calendar.month_abbr[month]} {year}",
                    total_classes=total,
                    attended_classes=attended,
                    percentage=round((attended / total) * 100, 1) if total else 0.0,
                )
            )
        return points

    async def request_correction(
        self, data: CorrectionRequestCreate, user_id: str
    ) -> CorrectionResponse:
        record = await self.repo.get_record_by_id(data.attendance_record_id)
        if not record:
            raise NotFoundError("Attendance record not found")

        corr = AttendanceCorrection(
            attendance_record_id=data.attendance_record_id,
            requested_by_user_id=user_id,
            old_status=record.status,
            new_status=data.new_status.upper(),
            reason=data.reason,
            status=ApprovalStatus.PENDING.value,
        )

        created = await self.repo.create_correction(corr)
        await self.db.commit()
        return _correction_to_response(created, str(record.student_id))

    async def approve_correction(
        self, correction_id: str, approve: bool, reviewer_id: str, rejection_reason: Optional[str] = None
    ) -> CorrectionResponse:
        corr = await self.repo.get_correction_by_id(correction_id)
        if not corr:
            raise NotFoundError("Attendance correction request not found")
        if corr.status != ApprovalStatus.PENDING.value:
            raise ValidationError("This correction request has already been reviewed")

        record = await self.repo.get_record_by_id(str(corr.attendance_record_id))
        if not record:
            raise NotFoundError("Attendance record not found")

        if approve:
            corr.status = ApprovalStatus.APPROVED.value
            record.status = corr.new_status
        else:
            corr.status = ApprovalStatus.REJECTED.value
            corr.rejection_reason = rejection_reason

        corr.reviewed_by_user_id = reviewer_id
        await self.db.commit()
        return _correction_to_response(corr, str(record.student_id))
