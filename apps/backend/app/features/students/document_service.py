"""Student document storage — Cloudinary edition.

All file storage is handled by Cloudinary. No files are written to local disk.
The ``StudentDocument`` model's ``storage_key`` column holds the Cloudinary
``public_id`` and ``file_url`` holds the ``secure_url``.  The ``stored_filename``
column is populated for backward-compatible display but is never used for I/O.

Threat model (unchanged from the local-disk version):
  * The extension is taken from an allow-list, not from the upload.
  * Size is enforced against actual bytes received, not Content-Length.
  * Files are served through an authenticated endpoint — possessing a URL
    alone is not enough.
"""
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.cloudinary_service import (
    DOCUMENT_TYPES as ALLOWED_CONTENT_TYPES_SET,
    IMAGE_TYPES,
    CloudinaryUploadError,
    CloudinaryUploadResult,
    delete_file as cloudinary_delete,
    upload_file as cloudinary_upload,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.enums import DocumentType
from app.features.auth.models import User
from app.features.students.profile_models import StudentDocument
from app.features.students.profile_schemas import DocumentResponse

# Map content types to canonical extensions (for stored_filename only).
CONTENT_TYPE_EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


class StudentDocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _to_response(row: StudentDocument, uploader_name: Optional[str]) -> DocumentResponse:
        return DocumentResponse(
            id=str(row.id),
            student_id=str(row.student_id),
            document_type=row.document_type,
            title=row.title,
            original_filename=row.original_filename,
            stored_filename=row.stored_filename,
            file_url=row.file_url,
            content_type=row.content_type,
            size_bytes=row.size_bytes,
            version=row.version,
            verification_status=row.verification_status,
            verified_by_name=None,
            verified_at=row.verified_at,
            rejection_reason=row.rejection_reason,
            uploaded_by_name=uploader_name,
            created_at=row.created_at,
        )

    async def list_documents(
        self, student_id: str, document_type: Optional[str] = None
    ) -> List[DocumentResponse]:
        query = (
            select(StudentDocument, User)
            .outerjoin(User, User.id == StudentDocument.uploaded_by_user_id)
            .where(
                StudentDocument.student_id == student_id,
                StudentDocument.deleted_at.is_(None),
            )
            .order_by(StudentDocument.created_at.desc())
        )
        if document_type:
            query = query.where(StudentDocument.document_type == document_type.upper())
        res = await self.db.execute(query)
        return [
            self._to_response(row, uploader.full_name if uploader else None)
            for row, uploader in res.all()
        ]

    async def upload(
        self,
        student_id: str,
        upload: UploadFile,
        document_type: str,
        title: Optional[str],
        uploaded_by_user_id: str,
    ) -> DocumentResponse:
        content_type = (upload.content_type or "").lower().split(";")[0].strip()
        if content_type not in ALLOWED_CONTENT_TYPES_SET:
            raise ValidationError(
                "Unsupported file type. Allowed: PDF, JPG, PNG, WEBP, DOC, DOCX."
            )

        doc_type = (document_type or DocumentType.OTHER.value).upper()
        if doc_type not in {d.value for d in DocumentType}:
            raise ValidationError(f"Unknown document type '{document_type}'.")

        # Determine the Cloudinary folder based on document type
        folder = self._resolve_folder(doc_type)

        # Upload to Cloudinary
        try:
            result: CloudinaryUploadResult = await cloudinary_upload(
                file=upload,
                folder=folder,
                allowed_types=ALLOWED_CONTENT_TYPES_SET,
                max_size_mb=settings.MAX_FILE_SIZE_MB,
            )
        except CloudinaryUploadError as exc:
            raise ValidationError(exc.message) from exc

        extension = CONTENT_TYPE_EXTENSIONS.get(content_type, "")
        stored_filename = f"{uuid.uuid4().hex}{extension}"

        row = StudentDocument(
            student_id=student_id,
            document_type=doc_type,
            title=title,
            original_filename=os.path.basename(upload.filename or "document")[:255],
            stored_filename=stored_filename,
            storage_key=result.public_id,
            file_url=result.secure_url,
            content_type=content_type,
            size_bytes=result.bytes,
            uploaded_by_user_id=uploaded_by_user_id,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)

        uploader = await self.db.get(User, uploaded_by_user_id)
        return self._to_response(row, uploader.full_name if uploader else None)

    async def get_document(self, student_id: str, document_id: str) -> StudentDocument:
        """Matched on id AND student_id, so a document id belonging to another
        student 404s instead of resolving."""
        res = await self.db.execute(
            select(StudentDocument).where(
                StudentDocument.id == document_id,
                StudentDocument.student_id == student_id,
                StudentDocument.deleted_at.is_(None),
            )
        )
        row = res.scalar_one_or_none()
        if not row:
            raise NotFoundError("Document not found")
        return row

    async def get_download_url(self, row: StudentDocument) -> str:
        """Return the Cloudinary secure_url for the document."""
        if not row.file_url:
            raise NotFoundError("No download URL available for this document")
        return row.file_url

    async def delete(self, student_id: str, document_id: str) -> None:
        row = await self.get_document(student_id, document_id)
        row.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Best-effort Cloudinary cleanup — the row is already soft-deleted
        # so a failed delete leaves an orphan to clean up, not a data
        # inconsistency.
        if row.storage_key:
            try:
                resource_type = "image" if row.content_type.startswith("image/") else "raw"
                await cloudinary_delete(row.storage_key, resource_type=resource_type)
            except Exception:
                # Metadata is already flagged deleted; an orphaned Cloudinary
                # asset is a cleanup concern, not a reason to fail the request.
                pass

    @staticmethod
    def _resolve_folder(doc_type: str) -> str:
        """Map a document type enum to a Cloudinary folder key."""
        mapping = {
            "PHOTO": "student_profile_photo",
            "RESUME": "resume",
            "CERTIFICATE": "certificate",
            "INTERNSHIP_LETTER": "certificate",
            "OFFER_LETTER": "certificate",
            "SSC_MEMO": "marksheet",
            "INTERMEDIATE_MEMO": "marksheet",
            "ACHIEVEMENT_PROOF": "certificate",
        }
        return mapping.get(doc_type, "student_document")
