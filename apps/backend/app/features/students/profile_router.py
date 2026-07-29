"""Student self-service profile endpoints.

Access model, enforced by which router prefix an operation lives under:

    /students/me/profile/...      the caller's OWN profile. The student id is
                                  resolved from the session token and is never
                                  accepted as a parameter, so there is no id to
                                  tamper with. Read + write.

    /students/{id}/profile/...    someone else's profile. Read for staff
                                  (counsellors scoped to assigned students via
                                  ensure_student_record_access); write for
                                  ADMIN only. The one exception is the
                                  counsellor observation on an interview, which
                                  is staff-authored by design.

A counsellor therefore has no route through which to modify a student's
personal, family, contact, skills or document records.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.core.enums import DocumentType
from app.core.exceptions import ForbiddenError, ValidationError
from app.core.permissions import require_permission
from app.core.scoping import ensure_student_record_access
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.features.students.document_service import StudentDocumentService
from app.features.students.profile_schemas import (
    AcademicRecordUpdate,
    AchievementCreate,
    AchievementResponse,
    AchievementUpdate,
    ContactInfoUpdate,
    CounsellorObservationUpdate,
    DocumentResponse,
    ExtracurricularUpdate,
    FamilyInfoUpdate,
    HealthInfoUpdate,
    InternshipCreate,
    InternshipResponse,
    InternshipUpdate,
    InterviewCreate,
    InterviewResponse,
    InterviewUpdate,
    PersonalInfoUpdate,
    PreferencesUpdate,
    SkillsGoalsUpdate,
    StudentCounsellingSummary,
    StudentSelfProfileResponse,
)
from app.features.students.profile_service import StudentProfileService
from app.features.students.repository import StudentRepository

router = APIRouter(prefix="/students", tags=["Student Profile"])

_ADMIN_ROLES = {"ADMIN", "SUPER_ADMIN"}


async def _self_student_id(current_user: User, db: AsyncSession) -> str:
    """The caller's own student id, from the token. Never a parameter."""
    service = StudentProfileService(db)
    return await service.resolve_student_id_for_user(str(current_user.id))


async def _ensure_staff_may_read(current_user: User, student_id: str, db: AsyncSession) -> None:
    await ensure_student_record_access(current_user, student_id, StudentRepository(db))


def _ensure_admin(current_user: User) -> None:
    """Writing to another person's profile is an administrative act. A
    counsellor holding student.read must not gain edit rights through it."""
    if not ({r.name for r in current_user.roles} & _ADMIN_ROLES):
        raise ForbiddenError("Only an administrator may edit another student's profile.")


# ==========================================================================
# Own profile — read
# ==========================================================================

@router.get("/me/profile", response_model=StudentSelfProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.get_self_profile(await _self_student_id(current_user, db))


# ==========================================================================
# Own profile — section updates
# ==========================================================================

@router.patch("/me/profile/personal", response_model=StudentSelfProfileResponse)
async def update_my_personal_info(
    data: PersonalInfoUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.update_personal(await _self_student_id(current_user, db), data)


@router.patch("/me/profile/family", response_model=StudentSelfProfileResponse)
async def update_my_family_info(
    data: FamilyInfoUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.update_family(await _self_student_id(current_user, db), data)


@router.patch("/me/profile/contact", response_model=StudentSelfProfileResponse)
async def update_my_contact_info(
    data: ContactInfoUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.update_contact(await _self_student_id(current_user, db), data)


@router.patch("/me/profile/skills", response_model=StudentSelfProfileResponse)
async def update_my_skills_and_goals(
    data: SkillsGoalsUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.update_skills_goals(await _self_student_id(current_user, db), data)


@router.patch("/me/profile/health", response_model=StudentSelfProfileResponse)
async def update_my_health_info(
    data: HealthInfoUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.update_health(await _self_student_id(current_user, db), data)


@router.patch("/me/profile/extracurricular", response_model=StudentSelfProfileResponse)
async def update_my_extracurricular(
    data: ExtracurricularUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.update_extracurricular(await _self_student_id(current_user, db), data)


@router.patch("/me/profile/preferences", response_model=StudentSelfProfileResponse)
async def update_my_preferences(
    data: PreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.update_preferences(await _self_student_id(current_user, db), data)


@router.post("/me/profile/photo", response_model=StudentSelfProfileResponse)
async def upload_my_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Profile photo upload.

    The image is uploaded to Cloudinary through the document pipeline, and
    ``photo_url`` is set to the returned Cloudinary ``secure_url``.  The photo
    is publicly accessible via the CDN URL but the upload endpoint itself
    requires authentication.
    """
    student_id = await _self_student_id(current_user, db)

    content_type = (file.content_type or "").lower().split(";")[0].strip()
    if content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise ValidationError("A profile photo must be a JPG, PNG or WEBP image.")

    documents = StudentDocumentService(db)
    stored = await documents.upload(
        student_id, file, DocumentType.PHOTO.value, "Profile photograph", str(current_user.id)
    )

    service = StudentProfileService(db)
    # Store the Cloudinary secure_url directly as the photo URL
    await service.set_photo_url(student_id, stored.file_url or f"/students/{student_id}/documents/{stored.id}/download")
    return await service.get_self_profile(student_id)


# ==========================================================================
# Counsellor section — the student's read-only view of staff notes
# ==========================================================================

@router.get("/me/counselling-summary", response_model=StudentCounsellingSummary)
async def get_my_counselling_summary(
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """Read-only by design: there is no matching write endpoint anywhere under
    /me, so a student cannot author or amend a counsellor's remark."""
    service = StudentProfileService(db)
    return await service.get_counselling_summary(await _self_student_id(current_user, db))


@router.get("/{student_id}/counselling-summary", response_model=StudentCounsellingSummary)
async def get_student_counselling_summary(
    student_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.read")),
    db: AsyncSession = Depends(get_async_db),
):
    await _ensure_staff_may_read(current_user, student_id, db)
    service = StudentProfileService(db)
    return await service.get_counselling_summary(student_id)


# ==========================================================================
# Own collections
# ==========================================================================

@router.get("/me/internships", response_model=List[InternshipResponse])
async def list_my_internships(
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.list_internships(await _self_student_id(current_user, db))


@router.post("/me/internships", response_model=InternshipResponse, status_code=status.HTTP_201_CREATED)
async def create_my_internship(
    data: InternshipCreate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.create_internship(await _self_student_id(current_user, db), data)


@router.patch("/me/internships/{item_id}", response_model=InternshipResponse)
async def update_my_internship(
    item_id: str,
    data: InternshipUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.update_internship(await _self_student_id(current_user, db), item_id, data)


@router.delete("/me/internships/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_internship(
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    await service.delete_internship(await _self_student_id(current_user, db), item_id)
    return None


@router.get("/me/interviews", response_model=List[InterviewResponse])
async def list_my_interviews(
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.list_interviews(await _self_student_id(current_user, db))


@router.post("/me/interviews", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def create_my_interview(
    data: InterviewCreate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.create_interview(await _self_student_id(current_user, db), data)


@router.patch("/me/interviews/{item_id}", response_model=InterviewResponse)
async def update_my_interview(
    item_id: str,
    data: InterviewUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.update_interview(await _self_student_id(current_user, db), item_id, data)


@router.delete("/me/interviews/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_interview(
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    await service.delete_interview(await _self_student_id(current_user, db), item_id)
    return None


@router.get("/me/achievements", response_model=List[AchievementResponse])
async def list_my_achievements(
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.list_achievements(await _self_student_id(current_user, db))


@router.post("/me/achievements", response_model=AchievementResponse, status_code=status.HTTP_201_CREATED)
async def create_my_achievement(
    data: AchievementCreate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.create_achievement(await _self_student_id(current_user, db), data)


@router.patch("/me/achievements/{item_id}", response_model=AchievementResponse)
async def update_my_achievement(
    item_id: str,
    data: AchievementUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    return await service.update_achievement(await _self_student_id(current_user, db), item_id, data)


@router.delete("/me/achievements/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_achievement(
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentProfileService(db)
    await service.delete_achievement(await _self_student_id(current_user, db), item_id)
    return None


# ==========================================================================
# Own documents
# ==========================================================================

@router.get("/me/documents", response_model=List[DocumentResponse])
async def list_my_documents(
    document_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentDocumentService(db)
    return await service.list_documents(await _self_student_id(current_user, db), document_type)


@router.post("/me/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_my_document(
    file: UploadFile = File(...),
    document_type: str = Form("OTHER"),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentDocumentService(db)
    return await service.upload(
        await _self_student_id(current_user, db),
        file,
        document_type,
        title,
        str(current_user.id),
    )


@router.delete("/me/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("profile.self.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    service = StudentDocumentService(db)
    await service.delete(await _self_student_id(current_user, db), document_id)
    return None


# ==========================================================================
# Staff views of a specific student
# ==========================================================================

@router.get("/{student_id}/profile", response_model=StudentSelfProfileResponse)
async def get_student_profile_detail(
    student_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.read")),
    db: AsyncSession = Depends(get_async_db),
):
    """Read-only for counsellors — this is the data that makes a counselling
    session useful. Scoped to assigned students."""
    await _ensure_staff_may_read(current_user, student_id, db)
    service = StudentProfileService(db)
    profile = await service.get_self_profile(student_id)
    # Aadhaar is a government identifier with no counselling purpose. Only the
    # student themself and an administrator ever see it.
    if not ({r.name for r in current_user.roles} & _ADMIN_ROLES):
        profile.aadhaar_number = None
        if not profile.share_contact_with_counsellor:
            profile.personal_email = None
            profile.alternate_phone = None
            profile.permanent_address = None
            profile.current_address = None
            # Health details ride the same consent switch as contact details.
            # A student who has withheld consent has withheld it for the more
            # sensitive block too, not just the less sensitive one.
            profile.medical_conditions = None
            profile.allergies = None
            profile.disability = None
            profile.current_medications = None
            profile.health_notes = None
    return profile


@router.get("/{student_id}/internships", response_model=List[InternshipResponse])
async def list_student_internships(
    student_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.read")),
    db: AsyncSession = Depends(get_async_db),
):
    await _ensure_staff_may_read(current_user, student_id, db)
    service = StudentProfileService(db)
    return await service.list_internships(student_id)


@router.get("/{student_id}/interviews", response_model=List[InterviewResponse])
async def list_student_interviews(
    student_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.read")),
    db: AsyncSession = Depends(get_async_db),
):
    await _ensure_staff_may_read(current_user, student_id, db)
    service = StudentProfileService(db)
    return await service.list_interviews(student_id)


@router.put("/{student_id}/interviews/{item_id}/observation", response_model=InterviewResponse)
async def set_interview_observation(
    student_id: str,
    item_id: str,
    data: CounsellorObservationUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("counselling.update")),
    db: AsyncSession = Depends(get_async_db),
):
    """The single staff write on student-owned data: coaching feedback on an
    interview. Deliberately its own endpoint and schema so it cannot carry any
    other field of the interview."""
    await _ensure_staff_may_read(current_user, student_id, db)
    service = StudentProfileService(db)
    return await service.set_counsellor_observation(
        student_id, item_id, data.counsellor_observation, str(current_user.id)
    )


@router.get("/{student_id}/achievements", response_model=List[AchievementResponse])
async def list_student_achievements(
    student_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.read")),
    db: AsyncSession = Depends(get_async_db),
):
    await _ensure_staff_may_read(current_user, student_id, db)
    service = StudentProfileService(db)
    return await service.list_achievements(student_id)


@router.get("/{student_id}/documents", response_model=List[DocumentResponse])
async def list_student_documents(
    student_id: str,
    document_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.read")),
    db: AsyncSession = Depends(get_async_db),
):
    await _ensure_staff_may_read(current_user, student_id, db)
    service = StudentDocumentService(db)
    return await service.list_documents(student_id, document_type)


@router.get("/{student_id}/documents/{document_id}/download")
async def download_student_document(
    student_id: str,
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.read")),
    db: AsyncSession = Depends(get_async_db),
):
    """Authenticated document download via redirect to Cloudinary.

    Access is still gated by ``ensure_student_record_access`` — the redirect
    only fires after the caller has passed the auth check.  The Cloudinary
    ``secure_url`` is a CDN-hosted URL; we redirect (302) to it so the
    client's browser fetches the file directly from the CDN.
    """
    await _ensure_staff_may_read(current_user, student_id, db)
    service = StudentDocumentService(db)
    row = await service.get_document(student_id, document_id)
    download_url = await service.get_download_url(row)
    return RedirectResponse(url=download_url, status_code=302)


@router.patch("/{student_id}/profile/personal", response_model=StudentSelfProfileResponse)
async def admin_update_student_personal(
    student_id: str,
    data: PersonalInfoUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.profile.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    _ensure_admin(current_user)
    service = StudentProfileService(db)
    return await service.update_personal(student_id, data)


@router.patch("/{student_id}/profile/family", response_model=StudentSelfProfileResponse)
async def admin_update_student_family(
    student_id: str,
    data: FamilyInfoUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.profile.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    _ensure_admin(current_user)
    service = StudentProfileService(db)
    return await service.update_family(student_id, data)


@router.patch("/{student_id}/profile/contact", response_model=StudentSelfProfileResponse)
async def admin_update_student_contact(
    student_id: str,
    data: ContactInfoUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.profile.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    _ensure_admin(current_user)
    service = StudentProfileService(db)
    return await service.update_contact(student_id, data)


@router.patch("/{student_id}/profile/academic", response_model=StudentSelfProfileResponse)
async def admin_update_student_academic_record(
    student_id: str,
    data: AcademicRecordUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permission("student.profile.manage")),
    db: AsyncSession = Depends(get_async_db),
):
    """The only writer for admission type, ABC id, entrance ranks, scholarship
    and credits-required. Deliberately has no /me counterpart: these are ERP
    facts, and a student editing their own EAMCET rank would be editing the
    basis of their scholarship eligibility."""
    _ensure_admin(current_user)
    service = StudentProfileService(db)
    return await service.update_academic_record(student_id, data)
