# Database Models & Migration Schema Documentation

This document documents the 48+ SQLAlchemy ORM database models, constraints, indexes, base mixins, and complete 13-migration history of the Student Counselling Management System (SCMS).

---

## 1. Base Mixins & Audit Design

All database entities in SCMS inherit from SQLAlchemy `Base` and standard mixins (`app/shared/models/base.py`):

- **`TimestampMixin`**: Adds timezone-aware `created_at` and `updated_at` columns updated automatically on database mutations.
- **`SoftDeleteMixin`**: Adds `deleted_at` timestamp. Queries filter out non-null `deleted_at` records by default to preserve auditability.
- **`AuditMixin`**: Adds `created_by`, `updated_by`, and optimistic concurrency locking integer `version`.

---

## 2. Domain Schema & Model Inventory (48 Entities)

### 2.1 Authentication & Identity Domain (`app.features.auth.models`)
1. **`User`**: Core identity table (`users`). Stores email, hashed password, name, department FK, active flag (`is_active`), and forced password change flag (`force_password_change`).
2. **`Role`**: Roles table (`roles`). Pre-seeded with `SUPER_ADMIN`, `ADMIN`, `HOD`, `COUNSELLOR`, `FACULTY`, `STUDENT`.
3. **`Permission`**: Granular system permissions (`permissions`).
4. **`user_roles`**: Association table mapping users to roles.
5. **`role_permissions`**: Association table mapping roles to permissions.
6. **`RefreshToken`**: Session tokens (`refresh_tokens`). Stores token secret hash, family UUID, rotation status, and revocation flags.
7. **`CounsellorAssignment`**: Active student-to-counsellor assignments (`counsellor_assignments`).

### 2.2 Academic Hierarchy Domain (`app.features.admin.models`)
8. **`Department`**: Academic departments (`departments`).
9. **`Section`**: Department section classes (`sections`).
10. **`AcademicYear`**: Academic calendar years (`academic_years`).
11. **`Semester`**: Fixed institutional 8-semester catalog (`semesters`, 1-1 through 4-2).
12. **`Subject`**: Curriculum courses (`subjects`).
13. **`SubjectFaculty`**: Faculty-to-subject assignment mappings (`subject_faculty`).

### 2.3 Student 360 & Self-Service Domain (`app.features.students.models` & `profile_models`)
14. **`StudentProfile`**: Core student record (`students`). Roll number, admission year, current section, risk level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
15. **`AcademicCorrectionRequest`**: Student grade/attendance correction tickets (`academic_correction_requests`).
16. **`AcademicCorrectionLog`**: Ticket audit history log (`academic_correction_logs`).
17. **`StudentProfile` (Self-Service)**: Profile extension (`student_profiles`). Personal, contact, health, and family details.
18. **`StudentCertification`**: Professional certifications (`student_certifications`).
19. **`StudentSkill`**: Technical & soft skills (`student_skills`).
20. **`StudentResearchPaper`**: Publications (`student_research_papers`).
21. **`StudentCompetition`**: Hackathons & competitions (`student_competitions`).
22. **`StudentClub`**: Extra-curricular club memberships (`student_clubs`).
23. **`StudentInternship`**: Industrial internships (`student_internships`).
24. **`StudentInterview`**: Campus placement interviews (`student_interviews`).
25. **`StudentAchievement`**: Academic & non-academic honors (`student_achievements`).
26. **`StudentDocument`**: Cloudinary document uploads (`student_documents`).
27. **`StudentProfileAuditLog`**: Self-service profile modification logs (`student_profile_audit_logs`).

### 2.4 Counselling Domain (`app.features.counselling.models`)
28. **`CounsellingSession`**: Session records (`counselling_sessions`). Immutable notes, category, sentiment, confidential notes.
29. **`SessionActionItem`**: Session action follow-ups (`session_action_items`). Assigned due dates and status (`PENDING`, `IN_PROGRESS`, `COMPLETED`, `OVERDUE`).

### 2.5 Attendance & Academics Domain (`app.features.attendance.models` & `academics.models`)
30. **`AttendanceRecord`**: Daily student class attendance (`attendance_records`). Status: `PRESENT`, `ABSENT`, `LATE`, `EXCUSED`.
31. **`AttendanceCorrection`**: Attendance mark correction requests (`attendance_corrections`).
32. **`AcademicMarks`**: Subject exam marks (`academic_marks`). Internal, mid-term, end-semester.
33. **`StudentBacklog`**: Subject backlog records (`student_backlogs`).

### 2.6 Reach Out / SRM Hub Domain (`app.features.reach_out.models`)
34. **`CounsellorContactProfile`**: Office location, cabin, office phone, WhatsApp, meeting links (`counsellor_contact_profiles`).
35. **`CommunicationTimelineLog`**: Interaction timeline history (`communication_timeline_logs`).
36. **`AppointmentRequest`**: Student appointment requests (`appointment_requests`).
37. **`StudentCommunicationPrivacy`**: Profile visibility & parent toggles (`student_communication_privacies`).
38. **`CounsellorFavoriteStudent`**: Pinned favorite students (`counsellor_favorite_students`).
39. **`InstitutionalChannelPolicy`**: Campus messaging policies (`institutional_channel_policies`).
40. **`CampusEmergencyContact`**: 24/7 hotline directory (`campus_emergency_contacts`).
41. **`ReachOutAuditLog`**: SRM configuration audit log (`reach_out_audit_logs`).

### 2.7 Office Import Engine & System Domain (`app.features.imports.models`, `audit.models`, `notifications.models`, `reports.models`)
42. **`ImportBatch`**: Spreadsheet job tracking (`import_batches`).
43. **`ImportRecord`**: Row-level parsing results (`import_records`).
44. **`AuditLog`**: System audit log (`audit_logs`). Action, entity_type, actor_id, changes JSON.
45. **`SystemSetting`**: Settings key-value store (`system_settings`).
46. **`Notification`**: In-app notifications (`notifications`).
47. **`ReportRecord`**: Report generation history (`report_records`).

---

## 3. Alembic Migration History (13 Migrations)

All migrations are located under `apps/backend/alembic/versions`:

1. `2026_07_21_1654-e9ecd609fe81_initial_schema.py`: Initial schema creation for core entities (Users, Roles, Departments, Sections, Students, Sessions).
2. `2026_07_25_2045-f3a9c7d21b44_fixed_semester_catalog.py`: Seeding 8-semester institutional catalog (1-1 to 4-2).
3. `2026_07_25_2130-a7c4e8f92d1b_section_study_year.py`: Addition of study year columns to section tables.
4. `2026_07_26_0930-b5d1f0c37a92_counselling_session_narrative.py`: Counselling session schema enhancements for long narratives and confidential notes.
5. `2026_07_26_0945-c8e2a1b46d03_student_gender_photo.py`: Addition of photo URL and gender columns to student profiles.
6. `2026_07_26_1015-d4f7b2e91c56_student_self_service_profile.py`: Creation of student self-service extension tables (Skills, Certifications, Publications, Internships).
7. `2026_07_26_1230-b1c2d3e4f5a6_reach_out_module.py`: Creation of Reach Out (SRM) hub schema.
8. `2026_07_26_1400-c2d3e4f5a6b7_reach_out_audit_logs.py`: Creation of `reach_out_audit_logs` table.
9. `2026_07_26_1800-d3e4f5a6b7c8_student_360_schema.py`: Student 360 overview stats schema.
10. `2026_07_26_2100-e4f5a6b7c8d9_office_import_module.py`: Creation of `import_batches` and `import_records` tables.
11. `2026_07_26_2200-e5f6a7b8c9d0_student_360_workspace.py`: Workspace tab state schema.
12. `2026_07_28_0000-f6a7b8c9d0e1_academic_correction_requests.py`: Creation of academic correction request and log tables.
13. `2026_07_31_0000-a7b8c9d0e1f2_vertex_interactions.py`: Creation of Vertex AI interaction logging tables for conversation history and tool usage tracking.
