import csv
import os
import uuid
from typing import Any, Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.core.events import event_bus, DomainEvent
from app.core.exceptions import NotFoundError
from app.features.reports.models import ReportRecord
from app.features.reports.repository import ReportRepository
from app.features.reports.schemas import ReportGenerateRequest, ReportRecordResponse
from app.features.admin.repository import AdminRepository
from app.features.attendance.repository import AttendanceRepository
from app.features.academics.repository import AcademicsRepository
from app.features.counselling.repository import CounsellingRepository
from app.features.students.repository import StudentRepository
from app.features.auth.repository import AuthRepository
from app.core.enums import TimelineEventType

ATTENDANCE_ALERT_THRESHOLD = 75.0


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ReportRepository(db)
        self.admin_repo = AdminRepository(db)
        self.attendance_repo = AttendanceRepository(db)
        self.academics_repo = AcademicsRepository(db)
        self.counselling_repo = CounsellingRepository(db)
        self.student_repo = StudentRepository(db)
        self.auth_repo = AuthRepository(db)
        self._student_cache: Dict[str, Any] = {}

    async def _student(self, student_id: str):
        if student_id not in self._student_cache:
            self._student_cache[student_id] = await self.student_repo.get_student_by_id(student_id)
        return self._student_cache[student_id]

    async def _gather_rows(self, report_type: str) -> Tuple[List[str], List[List[Any]]]:
        """Real, database-backed rows for the given report type. No fabricated data."""
        rt = report_type.upper()

        if rt == "DEPARTMENT":
            depts = await self.admin_repo.list_departments()
            return ["Code", "Name", "Description"], [[d.code, d.name, d.description or ""] for d in depts]

        if rt == "SEMESTER":
            semesters = await self.admin_repo.list_semesters()
            return (
                ["Number", "Name", "Start Date", "End Date", "Current"],
                [[s.number, s.name, s.start_date or "", s.end_date or "", "Yes" if s.is_current else "No"] for s in semesters],
            )

        if rt == "COUNSELLOR":
            counts = await self.counselling_repo.count_sessions_by_counsellor()
            rows = []
            for counsellor_id, count in counts:
                user = await self.auth_repo.get_user_by_id(counsellor_id)
                rows.append([user.full_name if user else counsellor_id, user.email if user else "", count])
            return ["Counsellor", "Email", "Sessions Conducted"], rows

        if rt == "ATTENDANCE":
            records = await self.attendance_repo.list_all_records()
            by_student: Dict[str, list] = {}
            for r in records:
                by_student.setdefault(str(r.student_id), []).append(r)

            rows = []
            for student_id, student_records in by_student.items():
                total = len(student_records)
                attended = sum(1 for r in student_records if r.status in ["PRESENT", "ON_DUTY"])
                pct = round((attended / total) * 100, 1) if total else 0.0
                if pct < ATTENDANCE_ALERT_THRESHOLD:
                    student = await self._student(student_id)
                    if student:
                        rows.append([student.roll_number, student.user.full_name if student.user else "Unknown", f"{pct}%"])
            rows.sort(key=lambda row: row[0])
            return ["Roll Number", "Student Name", "Attendance %"], rows

        if rt == "PERFORMANCE":
            histories = await self.academics_repo.list_all_sgpa_histories()
            rows = []
            for h in histories:
                student = await self._student(str(h.student_id))
                if student:
                    rows.append([student.roll_number, student.user.full_name if student.user else "Unknown", h.sgpa, h.cgpa])
            rows.sort(key=lambda row: row[0])
            return ["Roll Number", "Student Name", "SGPA", "CGPA"], rows

        if rt == "BACKLOG":
            backlogs = await self.academics_repo.list_all_active_backlogs()
            subjects = await self.admin_repo.get_subjects_by_ids([str(b.subject_id) for b in backlogs])
            subjects_by_id = {str(s.id): s for s in subjects}
            rows = []
            for b in backlogs:
                student = await self._student(str(b.student_id))
                subject = subjects_by_id.get(str(b.subject_id))
                if student:
                    rows.append([
                        student.roll_number,
                        student.user.full_name if student.user else "Unknown",
                        subject.code if subject else str(b.subject_id),
                        subject.name if subject else "",
                    ])
            rows.sort(key=lambda row: row[0])
            return ["Roll Number", "Student Name", "Subject Code", "Subject Name"], rows

        return ["Notice"], [["Unsupported report type — no data source configured for this report yet."]]

    def _write_csv(self, path: str, headers: List[str], rows: List[List[Any]]) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

    def _write_excel(self, path: str, headers: List[str], rows: List[List[Any]]) -> None:
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for row in rows:
            ws.append(row)
        wb.save(path)

    def _write_pdf(self, path: str, title: str, headers: List[str], rows: List[List[Any]]) -> None:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        doc = SimpleDocTemplate(path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

        table_data = [headers] + [[str(cell) for cell in row] for row in rows] if rows else [headers, ["No records found"]]
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
        doc.build(elements)

    async def generate_report(self, data: ReportGenerateRequest, user_id: str) -> ReportRecordResponse:
        import tempfile
        import cloudinary.uploader

        temp_dir = tempfile.gettempdir()
        file_format = data.file_format.upper()
        file_ext = {"CSV": "csv", "EXCEL": "xlsx", "PDF": "pdf"}.get(file_format, "csv")
        file_name = f"report_{data.report_type.lower()}_{uuid.uuid4().hex[:8]}.{file_ext}"
        file_path = os.path.join(temp_dir, file_name)

        headers, rows = await self._gather_rows(data.report_type)

        if file_format == "EXCEL":
            self._write_excel(file_path, headers, rows)
        elif file_format == "PDF":
            self._write_pdf(file_path, f"SCMS {data.report_type.title()} Report", headers, rows)
        else:
            self._write_csv(file_path, headers, rows)

        report_url = file_path
        try:
            resource_type = "raw" if file_format in ("CSV", "EXCEL") else "auto"
            res = cloudinary.uploader.upload(
                file_path,
                folder="vertex-erp/documents",
                resource_type=resource_type,
                use_filename=True,
                unique_filename=True,
            )
            report_url = res.get("secure_url", file_path)
        except Exception:
            report_url = file_path
        finally:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

        record = ReportRecord(
            report_type=data.report_type.upper(),
            generated_by_user_id=user_id,
            file_path=report_url,
            file_format=file_format,
            scope_metadata=data.scope_metadata,
        )

        created = await self.repo.save_report_record(record)
        await self.db.commit()

        await event_bus.publish(
            DomainEvent(
                type=TimelineEventType.REPORT_GENERATED.value,
                actor_id=user_id,
                metadata={"report_id": str(created.id), "type": created.report_type},
            )
        )

        return ReportRecordResponse.model_validate(created)

    async def list_reports(self, user_id: str) -> List[ReportRecordResponse]:
        records = await self.repo.list_user_reports(user_id)
        return [ReportRecordResponse.model_validate(r) for r in records]

    async def get_report_for_download(self, report_id: str, user_id: str) -> ReportRecord:
        record = await self.repo.get_report_by_id(report_id)
        if not record or str(record.generated_by_user_id) != user_id:
            raise NotFoundError("Report not found")
        if not record.file_path.startswith("http") and not os.path.isfile(record.file_path):
            raise NotFoundError("Report file is no longer available on the server")
        return record
