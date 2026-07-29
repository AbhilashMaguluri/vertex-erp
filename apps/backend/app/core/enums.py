from enum import Enum


class UserRole(str, Enum):
    STUDENT = "STUDENT"
    COUNSELLOR = "COUNSELLOR"
    FACULTY = "FACULTY"
    HOD = "HOD"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class StudentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    GRADUATED = "GRADUATED"
    DROPPED = "DROPPED"
    TRANSFERRED = "TRANSFERRED"


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    ON_DUTY = "ON_DUTY"
    MEDICAL_LEAVE = "MEDICAL_LEAVE"


class RiskLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FollowUpStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"


class SessionType(str, Enum):
    ACADEMIC = "ACADEMIC"
    PERSONAL = "PERSONAL"
    BEHAVIOURAL = "BEHAVIOURAL"
    CAREER = "CAREER"
    HEALTH = "HEALTH"
    FINANCIAL = "FINANCIAL"


class SessionMode(str, Enum):
    IN_PERSON = "IN_PERSON"
    PHONE = "PHONE"
    VIDEO_CALL = "VIDEO_CALL"


class CommunicationMode(str, Enum):
    PHONE_CALL = "PHONE_CALL"
    IN_PERSON = "IN_PERSON"
    EMAIL = "EMAIL"
    VIDEO_CALL = "VIDEO_CALL"


class CommunicationOutcome(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    CONCERNING = "CONCERNING"
    UNRESPONSIVE = "UNRESPONSIVE"


class BacklogStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLEARED = "CLEARED"


class NotificationPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class NotificationType(str, Enum):
    ATTENDANCE_ALERT = "ATTENDANCE_ALERT"
    FOLLOW_UP_REMINDER = "FOLLOW_UP_REMINDER"
    SESSION_CREATED = "SESSION_CREATED"
    APPROVAL_REQUEST = "APPROVAL_REQUEST"
    BROADCAST = "BROADCAST"
    SYSTEM = "SYSTEM"
    MARKS_PUBLISHED = "MARKS_PUBLISHED"
    PARENT_MEETING = "PARENT_MEETING"
    INTERVIEW_REMINDER = "INTERVIEW_REMINDER"
    DOCUMENT_PENDING = "DOCUMENT_PENDING"


class NotificationCategory(str, Enum):
    """The buckets the notification centre groups by. Stored on the row rather
    than derived at read time so re-categorising a type later doesn't silently
    rewrite the history of already-delivered notifications."""

    ACADEMIC = "ACADEMIC"
    COUNSELLING = "COUNSELLING"
    ATTENDANCE = "ATTENDANCE"
    PARENT_COMMUNICATION = "PARENT_COMMUNICATION"
    PLACEMENT = "PLACEMENT"
    SYSTEM = "SYSTEM"


# Default category for each notification type. Used when a notification is
# created without an explicit category.
NOTIFICATION_TYPE_CATEGORY = {
    NotificationType.ATTENDANCE_ALERT: NotificationCategory.ATTENDANCE,
    NotificationType.FOLLOW_UP_REMINDER: NotificationCategory.COUNSELLING,
    NotificationType.SESSION_CREATED: NotificationCategory.COUNSELLING,
    NotificationType.PARENT_MEETING: NotificationCategory.PARENT_COMMUNICATION,
    NotificationType.MARKS_PUBLISHED: NotificationCategory.ACADEMIC,
    NotificationType.INTERVIEW_REMINDER: NotificationCategory.PLACEMENT,
    NotificationType.DOCUMENT_PENDING: NotificationCategory.SYSTEM,
    NotificationType.APPROVAL_REQUEST: NotificationCategory.SYSTEM,
    NotificationType.BROADCAST: NotificationCategory.SYSTEM,
    NotificationType.SYSTEM: NotificationCategory.SYSTEM,
}


class DocumentType(str, Enum):
    RESUME = "RESUME"
    AADHAAR = "AADHAAR"
    PAN = "PAN"
    PASSPORT = "PASSPORT"
    BONAFIDE = "BONAFIDE"
    CERTIFICATE = "CERTIFICATE"
    INTERNSHIP_LETTER = "INTERNSHIP_LETTER"
    OFFER_LETTER = "OFFER_LETTER"
    ACHIEVEMENT_PROOF = "ACHIEVEMENT_PROOF"
    PHOTO = "PHOTO"
    # Admission-time documents a counselling/scholarship case actually needs.
    SSC_MEMO = "SSC_MEMO"
    INTERMEDIATE_MEMO = "INTERMEDIATE_MEMO"
    INCOME_CERTIFICATE = "INCOME_CERTIFICATE"
    CASTE_CERTIFICATE = "CASTE_CERTIFICATE"
    OTHER = "OTHER"


class AdmissionType(str, Enum):
    CONVENOR = "CONVENOR"
    MANAGEMENT = "MANAGEMENT"
    LATERAL_ENTRY = "LATERAL_ENTRY"


class SupportArea(str, Enum):
    """What a student says they want help with. Stored as a list on the
    profile and surfaced to the counsellor — this is the single most
    actionable thing a student can self-report, so it is a closed vocabulary
    rather than free text (OTHER carries the free-text companion field)."""

    ACADEMICS = "ACADEMICS"
    COMMUNICATION_SKILLS = "COMMUNICATION_SKILLS"
    FINANCIAL_SUPPORT = "FINANCIAL_SUPPORT"
    HIGHER_STUDIES = "HIGHER_STUDIES"
    PLACEMENTS = "PLACEMENTS"
    TIME_MANAGEMENT = "TIME_MANAGEMENT"
    MENTAL_WELLBEING = "MENTAL_WELLBEING"
    PERSONAL_ISSUES = "PERSONAL_ISSUES"
    ENTREPRENEURSHIP = "ENTREPRENEURSHIP"
    COMPETITIVE_EXAMS = "COMPETITIVE_EXAMS"
    OTHER = "OTHER"


class ExtracurricularActivity(str, Enum):
    NCC = "NCC"
    NSS = "NSS"
    SPORTS = "SPORTS"
    CULTURAL = "CULTURAL"
    CLUBS = "CLUBS"
    TECHNICAL_CLUBS = "TECHNICAL_CLUBS"
    HACKATHONS = "HACKATHONS"
    VOLUNTEERING = "VOLUNTEERING"
    EVENT_ORGANIZING = "EVENT_ORGANIZING"
    OTHER = "OTHER"


class AchievementCategory(str, Enum):
    HACKATHON = "HACKATHON"
    CERTIFICATION = "CERTIFICATION"
    COMPETITION = "COMPETITION"
    PUBLICATION = "PUBLICATION"
    AWARD = "AWARD"
    SPORTS = "SPORTS"
    CLUB = "CLUB"
    NSS_NCC = "NSS_NCC"
    VOLUNTEER = "VOLUNTEER"
    OTHER = "OTHER"


class InternshipStatus(str, Enum):
    APPLIED = "APPLIED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class InterviewType(str, Enum):
    ON_CAMPUS = "ON_CAMPUS"
    OFF_CAMPUS = "OFF_CAMPUS"
    VIRTUAL = "VIRTUAL"
    TELEPHONIC = "TELEPHONIC"
    TECHNICAL = "TECHNICAL"
    HR = "HR"
    GROUP_DISCUSSION = "GROUP_DISCUSSION"
    APTITUDE = "APTITUDE"


class InterviewResult(str, Enum):
    PENDING = "PENDING"
    SELECTED = "SELECTED"
    REJECTED = "REJECTED"
    ON_HOLD = "ON_HOLD"
    WITHDRAWN = "WITHDRAWN"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ARCHIVE = "ARCHIVE"
    RESTORE = "RESTORE"
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PASSWORD_RESET = "PASSWORD_RESET"


class TimelineEventType(str, Enum):
    STUDENT_REGISTERED = "STUDENT_REGISTERED"
    STUDENT_STATUS_CHANGED = "STUDENT_STATUS_CHANGED"
    STUDENT_PROMOTED = "STUDENT_PROMOTED"
    COUNSELLOR_ASSIGNED = "COUNSELLOR_ASSIGNED"
    COUNSELLOR_REASSIGNED = "COUNSELLOR_REASSIGNED"
    ATTENDANCE_UPDATED = "ATTENDANCE_UPDATED"
    ATTENDANCE_BELOW_THRESHOLD = "ATTENDANCE_BELOW_THRESHOLD"
    ATTENDANCE_CRITICAL = "ATTENDANCE_CRITICAL"
    MARKS_UPDATED = "MARKS_UPDATED"
    SGPA_CALCULATED = "SGPA_CALCULATED"
    BACKLOG_ADDED = "BACKLOG_ADDED"
    BACKLOG_CLEARED = "BACKLOG_CLEARED"
    SESSION_CONDUCTED = "SESSION_CONDUCTED"
    SESSION_ACKNOWLEDGED = "SESSION_ACKNOWLEDGED"
    FOLLOW_UP_CREATED = "FOLLOW_UP_CREATED"
    FOLLOW_UP_COMPLETED = "FOLLOW_UP_COMPLETED"
    FOLLOW_UP_OVERDUE = "FOLLOW_UP_OVERDUE"
    PARENT_COMMUNICATION = "PARENT_COMMUNICATION"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    RISK_FLAG_CHANGED = "RISK_FLAG_CHANGED"
    REPORT_GENERATED = "REPORT_GENERATED"


class CorrectionRequestStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ASSIGNED = "ASSIGNED"
    UNDER_REVIEW = "UNDER_REVIEW"
    NEED_MORE_INFO = "NEED_MORE_INFO"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

