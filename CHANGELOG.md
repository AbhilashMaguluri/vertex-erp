# Changelog — SCMS Enterprise Platform

## [2.1.0] - 2026-07-26

### Added
- **Complete Database-Driven Reach Out (SRM) Module**:
  - Fully database-driven Student Relationship Management & Reach Out Hub at `/reach-out`.
  - Multi-counsellor & department topology support (`Department -> Multiple Counsellors -> Assigned Students`).
  - Dynamic student assigned counsellor lookup via `CounsellorAssignment` (renders `"No counsellor has been assigned yet."` when unassigned).
  - Full Admin Management Desk allowing configuration of all 22 counsellor profile attributes (photo, office phone, mobile, WhatsApp, email, Teams, Zoom, Meet, Telegram, LinkedIn, office timings/schedule, availability status, cabin, building, floor, room, Google Maps location URL, languages, bio, experience, specializations).
  - Strict Pydantic backend validation for phone numbers, WhatsApp numbers, emails, and URLs returning HTTP 422 errors on invalid input.
  - Database Audit Logging system (`reach_out_audit_logs`) recording actor ID, action, target counsellor/contact, old values JSON, new values JSON, and timestamp.
  - Admin Emergency Hotlines Manager tab supporting dynamic CRUD for campus emergency contacts.
  - Real database analytics for Communication Health Index and Parent Engagement Scores without mock fallbacks (displays `"Insufficient data."` when data is missing).
  - Dynamic QR Code Generator using current window origin URL (`window.location.origin + '/reach-out?counsellor_id=' + id`).
  - HOD Department supervision mode allowing selection and inspection of any counsellor profile & caseload within the department.
  - Expanded automated pytest suite (`tests/test_reach_out.py`).
