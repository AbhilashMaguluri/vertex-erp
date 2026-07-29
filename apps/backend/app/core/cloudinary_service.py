"""Cloudinary file storage service.

Centralises all Cloudinary interactions behind a clean internal API. Every
upload, delete, and URL-generation call in the application goes through this
module — never through the SDK directly — so swapping providers later is a
single-file change.

Security:
    * The Cloudinary API secret is read from ``settings`` at import time and
      never leaked to any response body or log.
    * ``validate_file_type`` uses a strict allow-list, not a deny-list.
    * ``validate_file_size`` enforces limits against bytes already buffered
      (never from a client-provided Content-Length).
"""
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

import cloudinary
import cloudinary.api
import cloudinary.uploader
from fastapi import UploadFile

from app.config import settings

logger = logging.getLogger("app.cloudinary")

# ---------------------------------------------------------------------------
# SDK initialisation (runs once at import time)
# ---------------------------------------------------------------------------

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

# ---------------------------------------------------------------------------
# Folder constants
# ---------------------------------------------------------------------------

FOLDERS = {
    "student_profile_photo": "vertex-erp/student/profile-photos",
    "student_document": "vertex-erp/student/documents",
    "staff_profile_photo": "vertex-erp/staff/profile-photos",
    "certificate": "vertex-erp/certificates",
    "marksheet": "vertex-erp/marksheets",
    "resume": "vertex-erp/resumes",
    "general_document": "vertex-erp/documents",
}

# ---------------------------------------------------------------------------
# Allowed content types per category
# ---------------------------------------------------------------------------

IMAGE_TYPES: Set[str] = {"image/jpeg", "image/png", "image/webp"}

DOCUMENT_TYPES: Set[str] = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

ALL_ALLOWED_TYPES: Set[str] = IMAGE_TYPES | DOCUMENT_TYPES

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class CloudinaryUploadResult:
    """Metadata returned after a successful upload."""

    public_id: str
    secure_url: str
    format: str
    bytes: int
    resource_type: str
    original_filename: str
    width: Optional[int] = None
    height: Optional[int] = None


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class CloudinaryUploadError(Exception):
    """Raised when a Cloudinary upload fails."""

    def __init__(self, message: str = "File upload failed", detail: Optional[str] = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class CloudinaryDeleteError(Exception):
    """Raised when a Cloudinary deletion fails."""

    def __init__(self, message: str = "File deletion failed", detail: Optional[str] = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_file_type(content_type: str, allowed_types: Optional[Set[str]] = None) -> bool:
    """Return True if *content_type* is in the allow-list.

    Raises ``CloudinaryUploadError`` if the type is not allowed.
    """
    allowed = allowed_types or ALL_ALLOWED_TYPES
    normalised = content_type.lower().split(";")[0].strip()
    if normalised not in allowed:
        allowed_labels = ", ".join(sorted(allowed))
        raise CloudinaryUploadError(
            message="Unsupported file type",
            detail=f"Content type '{normalised}' is not allowed. Permitted: {allowed_labels}",
        )
    return True


def validate_file_size(size_bytes: int, max_mb: Optional[int] = None) -> bool:
    """Return True if *size_bytes* is within the limit.

    Raises ``CloudinaryUploadError`` if the file is too large.
    """
    limit_mb = max_mb or settings.MAX_FILE_SIZE_MB
    limit_bytes = limit_mb * 1024 * 1024
    if size_bytes > limit_bytes:
        raise CloudinaryUploadError(
            message=f"File exceeds the {limit_mb} MB limit",
            detail=f"Received {size_bytes} bytes ({size_bytes / (1024*1024):.1f} MB).",
        )
    if size_bytes == 0:
        raise CloudinaryUploadError(message="The uploaded file is empty")
    return True


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------


async def upload_file(
    file: UploadFile,
    folder: str,
    allowed_types: Optional[Set[str]] = None,
    max_size_mb: Optional[int] = None,
) -> CloudinaryUploadResult:
    """Upload a file to Cloudinary.

    Parameters
    ----------
    file:
        FastAPI ``UploadFile`` from the request.
    folder:
        Destination folder key from ``FOLDERS``, or an arbitrary path.
    allowed_types:
        Override for permitted MIME types.  Defaults to ``ALL_ALLOWED_TYPES``.
    max_size_mb:
        Override for the per-file size cap.  Defaults to ``settings.MAX_FILE_SIZE_MB``.

    Returns
    -------
    CloudinaryUploadResult
        Metadata about the uploaded asset.

    Raises
    ------
    CloudinaryUploadError
        On validation failure or Cloudinary SDK error.
    """
    content_type = (file.content_type or "").lower().split(";")[0].strip()
    validate_file_type(content_type, allowed_types)

    # Read the whole file into memory.  We already enforce a size limit
    # (default 10 MB) so this is safe.
    file_bytes = await file.read()
    validate_file_size(len(file_bytes), max_size_mb)

    # Resolve the folder path
    target_folder = FOLDERS.get(folder, folder)

    # Determine resource_type for Cloudinary
    resource_type = "image" if content_type.startswith("image/") else "raw"

    try:
        result = cloudinary.uploader.upload(
            file_bytes,
            folder=target_folder,
            resource_type=resource_type,
            # Use original filename (without extension) for friendlier URLs
            use_filename=True,
            unique_filename=True,
            overwrite=False,
        )
    except Exception as exc:
        logger.exception("Cloudinary upload failed")
        raise CloudinaryUploadError(
            message="File upload failed",
            detail=str(exc),
        ) from exc

    return CloudinaryUploadResult(
        public_id=result["public_id"],
        secure_url=result["secure_url"],
        format=result.get("format", ""),
        bytes=result.get("bytes", len(file_bytes)),
        resource_type=result.get("resource_type", resource_type),
        original_filename=result.get("original_filename", file.filename or "file"),
        width=result.get("width"),
        height=result.get("height"),
    )


async def delete_file(public_id: str, resource_type: str = "image") -> bool:
    """Delete an asset from Cloudinary by its public_id.

    Returns True on success.  Logs and raises ``CloudinaryDeleteError`` on failure.
    """
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        if result.get("result") == "ok":
            logger.info("Deleted Cloudinary asset: %s", public_id)
            return True
        # "not found" is not an error — the asset may have been removed already.
        if result.get("result") == "not found":
            logger.warning("Cloudinary asset not found (already deleted?): %s", public_id)
            return True
        logger.warning("Unexpected Cloudinary destroy result for %s: %s", public_id, result)
        return False
    except Exception as exc:
        logger.exception("Cloudinary delete failed for %s", public_id)
        raise CloudinaryDeleteError(
            message="File deletion failed",
            detail=str(exc),
        ) from exc


async def replace_file(
    old_public_id: Optional[str],
    file: UploadFile,
    folder: str,
    allowed_types: Optional[Set[str]] = None,
    max_size_mb: Optional[int] = None,
    old_resource_type: str = "image",
) -> CloudinaryUploadResult:
    """Replace an existing asset: upload the new file first, then delete the old one.

    Upload-first ordering means a Cloudinary outage during delete leaves us with
    an orphan to clean up, but never leaves the user without their file.
    """
    new_result = await upload_file(file, folder, allowed_types, max_size_mb)

    if old_public_id:
        try:
            await delete_file(old_public_id, resource_type=old_resource_type)
        except CloudinaryDeleteError:
            # The new file is already live; log the orphan and move on.
            logger.warning(
                "Failed to delete old Cloudinary asset %s after replacing with %s",
                old_public_id,
                new_result.public_id,
            )

    return new_result


def generate_secure_url(public_id: str, **transforms) -> str:
    """Build a Cloudinary delivery URL with optional transformations.

    Example transforms: ``width=300, height=300, crop='fill', quality='auto'``
    """
    url, _options = cloudinary.utils.cloudinary_url(
        public_id,
        secure=True,
        **transforms,
    )
    return url
