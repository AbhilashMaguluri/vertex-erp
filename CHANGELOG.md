# Changelog — SCMS Enterprise Platform

## [2.2.0] - 2026-08-01

### Fixed
- **Critical: passlib → direct bcrypt migration**: Dropped `passlib` dependency entirely. `passlib` 1.7.4 (last release 2020) probes the bcrypt backend with a >72-byte secret during initialization, which `bcrypt >= 5` rejects with `ValueError`. All password hashing and verification now uses `bcrypt` directly with explicit 72-byte truncation (`app/core/security.py`). This was the root cause of all `500 Internal Server Error` responses on login.
- **Auth logout cookie deletion**: Fixed `POST /api/v1/auth/logout` returning a fresh `Response(status_code=204)` which replaced the injected response object and dropped the `Set-Cookie` header that deletes the refresh token cookie. The revoked cookie was left sitting in the browser.
- **Rate limiter hardening**: Improved `RateLimitMiddleware` robustness for edge cases.

### Added
- **Vertex AI Engine expansion**: Added AI core modules — intent classification, goal-oriented planning, multi-tool orchestration, response evaluation, guardrails, ownership-scoped data access, and observability.
- **13th Alembic migration**: `2026_07_31_0000-a7b8c9d0e1f2_vertex_interactions.py` — Vertex AI interaction logging tables.
- **AI agent tools**: Profile lookup tool, records tool, correction tool, and UI action tool for the Vertex AI assistant.

---

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

---

## [2.0.0] - 2026-07-21

### Added
- Initial production release with Student 360, Counselling, Attendance, Academics, Admin, Notifications, Reports, Search, Parents, and Office Import modules.
- Full RBAC permission system with 6 roles and 20+ granular permissions.
- JWT access tokens + HttpOnly refresh token cookie rotation with theft detection.
- 12-section student self-service profile workspace.
- 5-step Office Import Engine for Excel/CSV spreadsheet ingestion.
- Docker Compose containerization with PostgreSQL 16.
