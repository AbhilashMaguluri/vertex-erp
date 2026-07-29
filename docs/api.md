# Complete API Endpoint Reference

This document provides a comprehensive reference for all 158 HTTP REST and SSE endpoints implemented across 16 FastAPI routers in the backend application.

---

## 1. Health & Observability (`/api/v1/health`)

| Route | Method | Auth / Permission | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/health/live` | `GET` | Public | Liveness probe: returns HTTP 200 if app process is running. |
| `/api/v1/health/ready` | `GET` | Public | Readiness probe: verifies DB connectivity & free disk space (>1GB). Returns HTTP 530 if unhealthy. |
| `/api/v1/health/startup` | `GET` | Public | Startup probe: verifies database connectivity and initial migration state. |

---

## 2. Authentication & Sessions (`/api/v1/auth`)

| Route | Method | Auth / Permission | Request Payload / Description | Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/auth/login` | `POST` | Public | `LoginRequest` `{email, password}` | `TokenResponse` + Sets HttpOnly cookie |
| `/api/v1/auth/refresh` | `POST` | Refresh Cookie | None (reads HttpOnly Cookie) | `TokenResponse` + Rotates HttpOnly cookie |
| `/api/v1/auth/logout` | `POST` | Refresh Cookie | None | HTTP 204 No Content + Clears cookie |
| `/api/v1/auth/me` | `GET` | Authenticated | None | `UserProfileResponse` |
| `/api/v1/auth/change-password` | `POST` | Authenticated | `ChangePasswordRequest` | HTTP 204 No Content |
| `/api/v1/auth/forgot-password` | `POST` | Public | `ForgotPasswordRequest` | `{"message": "..."}` |
| `/api/v1/auth/reset-password` | `POST` | Public | `ResetPasswordRequest` | `{"message": "..."}` |
| `/api/v1/auth/sessions` | `GET` | Authenticated | None | `List[SessionResponse]` |
| `/api/v1/auth/sessions/{id}` | `DELETE`| Authenticated | Path: `session_id` | HTTP 204 No Content |

---

## 3. Administration & Academic Config (`/api/v1/admin`)

| Route | Method | Auth / Permission | Request / Query | Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/admin/departments` | `POST` | `department.manage` | `DepartmentCreate` | `DepartmentResponse` (201 Created) |
| `/api/v1/admin/departments` | `GET` | Authenticated | None | `List[DepartmentResponse]` |
| `/api/v1/admin/departments/{id}`| `PATCH` | `department.manage` | `DepartmentUpdate` | `DepartmentResponse` |
| `/api/v1/admin/sections` | `POST` | `section.manage` | `SectionCreate` | `SectionResponse` (201 Created) |
| `/api/v1/admin/sections` | `GET` | Authenticated | Query: `department_id` (opt) | `List[SectionResponse]` |
| `/api/v1/admin/sections/{id}` | `PATCH` | `section.manage` | `SectionUpdate` | `SectionResponse` |
| `/api/v1/admin/sections/{id}` | `DELETE`| `section.manage` | None | HTTP 204 No Content |
| `/api/v1/admin/academic-years` | `POST` | `academic.manage` | `AcademicYearCreate` | `AcademicYearResponse` (201 Created) |
| `/api/v1/admin/academic-years` | `GET` | Authenticated | None | `List[AcademicYearResponse]` |
| `/api/v1/admin/academic-years/{id}`|`PATCH`| `academic.manage` | `AcademicYearUpdate` | `AcademicYearResponse` |
| `/api/v1/admin/semesters` | `GET` | Authenticated | None | `List[SemesterResponse]` (Fixed catalog 1-1..4-2)|
| `/api/v1/admin/subjects` | `POST` | `subject.manage` | `SubjectCreate` | `SubjectResponse` (201 Created) |
| `/api/v1/admin/subjects` | `GET` | Authenticated | Query: `department_id` (opt) | `List[SubjectResponse]` |
| `/api/v1/admin/subjects/{id}` | `PATCH` | `subject.manage` | `SubjectUpdate` | `SubjectResponse` |
| `/api/v1/admin/users` | `POST` | `user.manage` | `UserCreateRequest` | `AdminCreateUserResponse` (201 Created) |
| `/api/v1/admin/users` | `GET` | `user.manage` | Query: `role`, `search`, `page` | `PaginatedResponse[UserListItemResponse]` |
| `/api/v1/admin/users/{id}` | `GET` | `user.manage` | None | `UserProfileResponse` |
| `/api/v1/admin/users/{id}` | `PATCH` | `user.manage` | `UserUpdateRequest` | `UserProfileResponse` |
| `/api/v1/admin/users/{id}/deactivate`|`POST`| `user.manage` | None | HTTP 204 No Content |
| `/api/v1/admin/users/{id}/activate` |`POST` | `user.manage` | None | HTTP 204 No Content |
| `/api/v1/admin/users/{id}/reset-password`|`POST`|`user.manage`| None | `AdminResetPasswordResponse` |
| `/api/v1/admin/users/{id}/sessions`|`GET` | `user.manage` | None | `List[SessionResponse]` |
| `/api/v1/admin/users/{id}/force-logout`|`POST`|`user.manage`| None | HTTP 204 No Content |
| `/api/v1/admin/users/assign-counsellor`|`POST`|`user.manage`| `AssignCounsellorRequest`| HTTP 204 No Content |

---

## 4. Office Spreadsheet Import Engine (`/api/v1/admin/imports`)

| Route | Method | Auth / Permission | Request Payload / Description | Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/admin/imports` | `GET` | `user.manage` | Query: `limit` (default 20) | `ImportHistoryResponse` |
| `/api/v1/admin/imports/sample-template.xlsx`| `GET` | `user.manage` | Download office XLSX template | Binary File Attachment (`.xlsx`) |
| `/api/v1/admin/imports/analyze` | `POST` | `user.manage` | `file`: UploadFile (Excel/CSV) | `ImportPreviewResponse` (201 Created) |
| `/api/v1/admin/imports/{batch_id}/preview`| `GET` | `user.manage` | None | `ImportPreviewResponse` |
| `/api/v1/admin/imports/{batch_id}/execute`| `POST` | `user.manage` | `ImportConfiguration` payload | `ImportProgressResponse` (202 Accepted) |
| `/api/v1/admin/imports/{batch_id}/progress`| `GET` | `user.manage` | None (Poll progress) | `ImportProgressResponse` |
| `/api/v1/admin/imports/{batch_id}` | `GET` | `user.manage` | None | `ImportSummaryResponse` |
| `/api/v1/admin/imports/{batch_id}/credentials`|`GET`| `user.manage` | Query: `limit` (default 50) | `List[GeneratedCredential]` |
| `/api/v1/admin/imports/{batch_id}/credentials.xlsx`|`GET`|`user.manage`| Download issued logins workbook | Binary File Attachment (`.xlsx`) |
| `/api/v1/admin/imports/{batch_id}/credentials`|`DELETE`|`user.manage`| Purge temporary passwords | HTTP 204 No Content |
| `/api/v1/admin/imports/{batch_id}/report.xlsx`|`GET`|`user.manage`| Excel audit summary report | Binary File Attachment (`.xlsx`) |
| `/api/v1/admin/imports/{batch_id}/report.pdf`|`GET` |`user.manage` | PDF audit summary report | Binary File Attachment (`.pdf`) |

---

## 5. Student Workspace & Self-Service Profiles (`/api/v1/students`)

| Route | Method | Auth / Permission | Request / Query | Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/students/me/profile` | `GET` | `profile.self.manage` | None | `StudentSelfProfileResponse` |
| `/api/v1/students/me/profile/personal`| `PATCH` | `profile.self.manage` | Personal fields DTO | `StudentSelfProfileResponse` |
| `/api/v1/students/me/profile/family` | `PATCH` | `profile.self.manage` | Family fields DTO | `StudentSelfProfileResponse` |
| `/api/v1/students/me/profile/contact` | `PATCH` | `profile.self.manage` | Contact fields DTO | `StudentSelfProfileResponse` |
| `/api/v1/students/me/profile/skills` | `PATCH` | `profile.self.manage` | Skills & certifications DTO | `StudentSelfProfileResponse` |
| `/api/v1/students/me/profile/health` | `PATCH` | `profile.self.manage` | Health & emergency DTO | `StudentSelfProfileResponse` |
| `/api/v1/students/me/profile/extracurricular`|`PATCH`|`profile.self.manage`| Clubs & competitions DTO | `StudentSelfProfileResponse` |
| `/api/v1/students/me/profile/preferences`|`PATCH`|`profile.self.manage`| Privacy preferences DTO | `StudentSelfProfileResponse` |
| `/api/v1/students/me/profile/photo` | `POST` | `profile.self.manage` | `file`: UploadFile (Image) | `StudentSelfProfileResponse` |
| `/api/v1/students/me/counselling-summary`|`GET`| Authenticated | None | `StudentCounsellingSummary` |
| `/api/v1/students/{id}/counselling-summary`|`GET`| `counselling.read` | None | `StudentCounsellingSummary` |
| `/api/v1/students/me/internships` | `GET` | `profile.self.manage` | None | `List[InternshipResponse]` |
| `/api/v1/students/me/internships` | `POST` | `profile.self.manage` | `InternshipCreate` | `InternshipResponse` (201 Created) |
| `/api/v1/students/me/internships/{item_id}`|`PATCH`|`profile.self.manage`| `InternshipUpdate` | `InternshipResponse` |
| `/api/v1/students/me/internships/{item_id}`|`DELETE`|`profile.self.manage`| None | HTTP 204 No Content |
| `/api/v1/students/me/interviews` | `GET` | `profile.self.manage` | None | `List[InterviewResponse]` |
| `/api/v1/students/me/interviews` | `POST` | `profile.self.manage` | `InterviewCreate` | `InterviewResponse` (201 Created) |
| `/api/v1/students/me/interviews/{item_id}`|`PATCH`|`profile.self.manage`| `InterviewUpdate` | `InterviewResponse` |
| `/api/v1/students/me/interviews/{item_id}`|`DELETE`|`profile.self.manage`| None | HTTP 204 No Content |
| `/api/v1/students/me/achievements` | `GET` | `profile.self.manage` | None | `List[AchievementResponse]` |
| `/api/v1/students/me/achievements` | `POST` | `profile.self.manage` | `AchievementCreate` | `AchievementResponse` (201 Created) |
| `/api/v1/students/me/achievements/{item_id}`|`PATCH`|`profile.self.manage`| `AchievementUpdate` | `AchievementResponse` |
| `/api/v1/students/me/achievements/{item_id}`|`DELETE`|`profile.self.manage`| None | HTTP 204 No Content |
| `/api/v1/students/me/documents` | `GET` | `profile.self.manage` | None | `List[DocumentResponse]` |
| `/api/v1/students/me/documents` | `POST` | `profile.self.manage` | `file`: UploadFile + meta | `DocumentResponse` (201 Created) |
| `/api/v1/students/me/documents/{doc_id}`|`DELETE`|`profile.self.manage`| None | HTTP 204 No Content |
| `/api/v1/students/{id}/profile` | `GET` | `student.read` | None | `StudentSelfProfileResponse` |
| `/api/v1/students/{id}/internships` | `GET` | `student.read` | None | `List[InternshipResponse]` |
| `/api/v1/students/{id}/interviews` | `GET` | `student.read` | None | `List[InterviewResponse]` |
| `/api/v1/students/{id}/interviews/{item_id}/observation`|`PUT`|`counselling.create`| Observation text payload | `InterviewResponse` |
| `/api/v1/students/{id}/achievements` | `GET` | `student.read` | None | `List[AchievementResponse]` |
| `/api/v1/students/{id}/documents` | `GET` | `student.read` | None | `List[DocumentResponse]` |
| `/api/v1/students/{id}/documents/{doc_id}/download`|`GET`|`student.read`| None | File Download / Redirect |
| `/api/v1/students/caseload` | `GET` | `student.caseload.read`| Search, filters, page | `PaginatedResponse[CaseloadStudentResponse]`|
| `/api/v1/students/caseload/facets` | `GET` | `student.caseload.read`| None | `CaseloadFacets` |
| `/api/v1/students/{id}/session-context`|`GET`| `counselling.read` | None | `SessionContextResponse` |
| `/api/v1/students/roster` | `GET` | `student.read` | Query: `section_id` | `List[RosterStudentResponse]` |
| `/api/v1/students/me/workspace` | `GET` | Authenticated | None | `Student360Response` |
| `/api/v1/students/{id}/workspace` | `GET` | `student.read` | None | `Student360Response` |
| `/api/v1/students/{id}` | `GET` | `student.read` | None | `StudentProfileResponse` |
| `/api/v1/students/{id}/360/personal` | `GET` | `student.read` | None | `Student360Response` |
| `/api/v1/students/{id}/360/academic` | `GET` | `student.read` | None | `Student360Response` |
| `/api/v1/students/{id}/risk` | `PATCH` | `student.risk.manage` | `RiskFlagUpdateRequest` | `StudentProfileResponse` |
| `/api/v1/students/me/academic-corrections`|`POST`| Authenticated | `AcademicCorrectionCreate` | `AcademicCorrectionResponse` (201) |
| `/api/v1/students/me/academic-corrections`|`GET`| Authenticated | None | `List[AcademicCorrectionResponse]` |
| `/api/v1/students/academic-corrections/caseload`|`GET`|`counselling.read`| None | `List[AcademicCorrectionResponse]` |
| `/api/v1/students/academic-corrections/{req_id}`|`GET`| Authenticated | None | `AcademicCorrectionResponse` |
| `/api/v1/students/academic-corrections/{req_id}/review`|`PATCH`|`counselling.create`|`AcademicCorrectionReview`|`AcademicCorrectionResponse` |
| `/api/v1/students/academic-corrections/{req_id}/clarification`|`POST`|Authenticated|`AcademicCorrectionClarification`|`AcademicCorrectionResponse`|

---

## 6. Counselling Sessions & Follow-ups (`/api/v1/counselling`)

| Route | Method | Auth / Permission | Request Payload / Query | Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/counselling/dashboard` | `GET` | `counselling.read` | Query: `counsellor_id` (Admin/HOD) | `CounsellorDashboardResponse` |
| `/api/v1/counselling/sessions` | `POST` | `counselling.create` | `SessionCreateRequest` | `SessionResponse` (201 Created) |
| `/api/v1/counselling/sessions` | `GET` | `counselling.read` | Query: `student_id`, `page` | `List[SessionResponse]` |
| `/api/v1/counselling/my-sessions` | `GET` | `counselling.acknowledge`| Query: `page`, `per_page` | `List[SessionResponse]` (Strips confidential notes)|
| `/api/v1/counselling/sessions/{id}` | `GET` | `counselling.read` | None | `SessionResponse` |
| `/api/v1/counselling/follow-ups` | `GET` | `counselling.read` | Query: `status`, `counsellor_id`| `List[ActionItemResponse]` |
| `/api/v1/counselling/follow-ups/{id}/status`|`PATCH`|`counselling.update`| `FollowUpStatusUpdateRequest`| `ActionItemResponse` |
| `/api/v1/counselling/follow-ups/{id}` | `PATCH` | `counselling.update` | `FollowUpUpdateRequest` | `ActionItemResponse` |
| `/api/v1/counselling/sessions/{id}/acknowledge`|`POST`|`counselling.acknowledge`| None | `SessionResponse` |

---

## 7. Attendance Management (`/api/v1/attendance`)

| Route | Method | Auth / Permission | Request Body / Query | Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/attendance` | `POST` | `attendance.create` | `BulkAttendanceCreate` | `List[AttendanceRecordResponse]` (201) |
| `/api/v1/attendance/student/{id}` | `GET` | `attendance.read` | Ownership-scoped | `StudentAttendanceSummaryResponse` |
| `/api/v1/attendance/corrections` | `POST` | `attendance.correction.create`| `CorrectionRequestCreate` | `CorrectionResponse` (201 Created) |
| `/api/v1/attendance/corrections/{id}`|`PATCH`|`attendance.correction.approve`| `is_approved`, `rejection_reason`| `CorrectionResponse` |

---

## 8. Academic Management & Marks (`/api/v1/academics`)

| Route | Method | Auth / Permission | Request / Query | Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/academics/student/{id}/record`|`GET`| `academics.read` | Ownership-scoped | `StudentAcademicRecordResponse` |
| `/api/v1/marks` | `POST` | `marks.create` | `BulkMarksCreate` | `List[MarksResponse]` (201 Created) |
| `/api/v1/academics/student/{id}/backlogs`|`GET`| `academics.read` | Ownership-scoped | `List[BacklogResponse]` |
| `/api/v1/academics/student/{id}/gpa/calculate`|`POST`|`academics.read`| Query: `semester_id` | `SGPACalculationResponse` |

---

## 9. Parent Communication (`/api/v1/parent-communication`)

| Route | Method | Auth / Permission | Request Body | Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/parent-communication` | `POST` | `parent_communication.create`| `ParentCommunicationCreateRequest`| `ParentCommunicationResponse` (201) |
| `/api/v1/parent-communication/student/{id}`|`GET`|`parent_communication.read`| Ownership-scoped | `List[ParentCommunicationResponse]` |

---

## 10. Notification Center (`/api/v1/notifications`)

| Route | Method | Auth / Permission | Query Params | Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/notifications` | `GET` | Authenticated | `unread_only`, `category`, `page` | `List[NotificationResponse]` |
| `/api/v1/notifications/summary` | `GET` | Authenticated | None | `NotificationSummaryResponse` |
| `/api/v1/notifications/unread-count` | `GET` | Authenticated | None | `NotificationUnreadCountResponse` |
| `/api/v1/notifications/{id}/read` | `PATCH` | Authenticated | None | `NotificationResponse` |
| `/api/v1/notifications/read-all` | `PATCH` | Authenticated | None | HTTP 204 No Content |

---

## 11. Reports & Exports (`/api/v1/reports`)

| Route | Method | Auth / Permission | Request Body | Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/reports/generate` | `POST` | `report.generate` | `ReportGenerateRequest` | `ReportRecordResponse` (201 Created) |
| `/api/v1/reports/history` | `GET` | `report.download` | None | `List[ReportRecordResponse]` |
| `/api/v1/reports/{id}/download` | `GET` | `report.download` | None | File Download Response / 302 Redirect |

---

## 12. Audit Logs & Settings (`/api/v1/audit`, `/api/v1/settings`)

| Route | Method | Auth / Permission | Query / Body | Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/admin/audit-logs` | `GET` | `audit.read` | Query: `action`, `entity_type`, `user_id`| `List[AuditLogResponse]` |
| `/api/v1/settings/{section}` | `GET` | `settings.manage` | Path: section name (1-12) | `List[SystemSettingResponse]` |
| `/api/v1/settings/{section}/{key}`| `PUT` | `settings.manage` | `SystemSettingUpdateRequest` | `SystemSettingResponse` |

---

## 13. Global Search (`/api/v1/search`)

| Route | Method | Auth / Permission | Query Params | Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/search` | `GET` | Authenticated | `q`: min length 1 | `List[SearchResultItem]` |

---

## 14. Reach Out / SRM Hub (`/api/v1/reach-out`)

| Route | Method | Auth / Permission | Payload / Description | Response / Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/reach-out/my-counsellor` | `GET` | Student | Active counsellor profile lookup | `{"assigned": true/false, "profile": ...}` |
| `/api/v1/reach-out/counsellors` | `GET` | Authenticated | Department filter (HOD scoped) | `List[CounsellorContactProfileSchema]` |
| `/api/v1/reach-out/counsellors/{id}` | `GET` | Authenticated | None | `CounsellorContactProfileSchema` |
| `/api/v1/reach-out/caseload` | `GET` | Counsellor/HOD/Admin| Retrieve assigned caseload + metrics | `List[AssignedStudentContactSchema]` |
| `/api/v1/reach-out/caseload/{id}/ai-briefing`|`GET`| Counsellor | Pre-meeting AI synthesis briefing | `AIMeetingBriefingResponse` |
| `/api/v1/reach-out/favorites/{id}` | `POST` | Counsellor | Pin student to favorites rail | `{"message": "Student pinned as favorite."}` |
| `/api/v1/reach-out/favorites/{id}` | `DELETE`| Counsellor | Unpin student from favorites rail | `{"message": "Student unpinned from favorites."}`|
| `/api/v1/reach-out/caseload/{id}/timeline`|`GET` | Counsellor | Communication history log | `List[CommunicationTimelineLogResponse]` |
| `/api/v1/reach-out/caseload/{id}/timeline`|`POST`| Counsellor | `CommunicationTimelineLogCreate` | `CommunicationTimelineLogResponse` |
| `/api/v1/reach-out/appointments` | `GET` | Authenticated | Student/Counsellor appointments | `List[AppointmentRequestResponse]` |
| `/api/v1/reach-out/appointments` | `POST` | Student | `AppointmentRequestCreate` | `AppointmentRequestResponse` |
| `/api/v1/reach-out/appointments/{id}/status`|`PUT`| Counsellor | `AppointmentRequestStatusUpdate`| `AppointmentRequestResponse` |
| `/api/v1/reach-out/privacy` | `GET` | Student | Get profile sharing & parent toggles | `StudentPrivacySettingsSchema` |
| `/api/v1/reach-out/privacy` | `PUT` | Student | Update profile sharing & parent toggles | `StudentPrivacySettingsSchema` |
| `/api/v1/reach-out/templates` | `GET` | Counsellor | Quick message template directory | `List[CommunicationTemplateResponse]` |
| `/api/v1/reach-out/emergency-contacts`|`GET` | Public | Campus emergency hotline directory | `List[CampusEmergencyContactSchema]` |
| `/api/v1/reach-out/admin/emergency-contacts`|`POST`| Admin | `CampusEmergencyContactCreate` | `CampusEmergencyContactSchema` |
| `/api/v1/reach-out/admin/emergency-contacts/{id}`|`DELETE`| Admin | Delete emergency hotline contact | `{"message": "Emergency contact deleted."}` |
| `/api/v1/reach-out/channel-policy` | `GET` | Authenticated | Institutional messaging policies | `InstitutionalChannelPolicySchema` |
| `/api/v1/reach-out/admin/channel-policy`|`PUT` | Admin | `InstitutionalChannelPolicySchema`| `InstitutionalChannelPolicySchema` |
| `/api/v1/reach-out/admin/audit-logs` | `GET` | Admin | Reach Out configuration audit trail | `List[ReachOutAuditLogResponse]` |
| `/api/v1/reach-out/admin/counsellors/{id}`|`PUT` | Admin | `CounsellorContactProfileUpdate` | `CounsellorContactProfileSchema` |

---

## 15. Vertex AI Engine (`/api/vertex`)

| Route | Method | Auth / Permission | Request Payload | Response / Media Type |
| :--- | :--- | :--- | :--- | :--- |
| `/api/vertex/message` | `POST` | Authenticated | `VertexRequest` `{message, context}` | `text/event-stream` (Server-Sent Events) |

### SSE Event Stream Wire Payload Examples:

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no

data: {"type": "token", "content": "Hello"}

data: {"type": "token", "content": ", analyzing student record..."}

data: {"type": "action", "action": {"target": "/students/uuid-123", "label": "Open Student 360 Workspace"}}

data: {"type": "done"}
```
