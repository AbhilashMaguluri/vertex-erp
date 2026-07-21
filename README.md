# Student Counselling Management System (SCMS) — Enterprise Platform

> **Version:** 2.0.0  
> **Architecture:** Clean Architecture + Event-Driven Monorepo  
> **Frontend Stack:** React 19 + TypeScript + Vite + Tailwind CSS v4 + shadcn/ui + TanStack Query  
> **Backend Stack:** FastAPI (Python 3.12) + Async SQLAlchemy 2.0 + Alembic + Pydantic v2 + PostgreSQL  

---

## 🌟 Executive Summary & Vision

The **Student Counselling Management System (SCMS)** is an enterprise-grade SaaS application engineered to replace physical counselling registers, paperwork, and fragmented spreadsheets used across higher-education colleges and universities.

Instead of generic ERP menu systems, SCMS adopts a **workspace-oriented mental model** organized around role-specific environments. The application’s signature feature is the **Student 360° Workspace** — a single unified hub containing attendance trends, academic trajectories, immutable counselling session records, parent call logs, uploaded documents, reports, and risk indicators without context switching.

---

## 🏗️ Core Architectural Pillars

1. **Workspace-Oriented Navigation** — Users do not click through menu trees. They enter role-tailored workspaces (Student Workspace, Counsellor Workspace, Faculty Workspace, Department Workspace, Administration Workspace).
2. **Actionable Dashboards** — Every dashboard prioritizes actionable items:
   - **🔴 Attention Required** (at-risk students, critical attendance alerts, overdue follow-ups)
   - **📋 Today's Tasks** (scheduled sessions, callbacks)
   - **⚡ Quick Actions** (1-click session creation, parent call logging, report generation)
   - **📈 Insights & Analytics** (trend sparklines, section comparisons)
   - **🕐 Recent Activity Feed** (chronological event stream)
3. **Student 360° Workspace (Signature Feature)** — A single unified view featuring 9 tabbed modules:
   - `Overview` | `Timeline` | `Attendance` | `Academics` | `Counselling` | `Parent Calls` | `Documents` | `Reports` | `Analytics`
4. **Universal Timeline System** — Chronological event stream for all 20+ domain events (`STUDENT_REGISTERED`, `ATTENDANCE_BELOW_THRESHOLD`, `MARKS_UPDATED`, `SESSION_CONDUCTED`, `RISK_FLAG_CHANGED`, `PARENT_COMMUNICATION`).
5. **Historical Data Everywhere** — Metrics show time-series trends and sparklines rather than static snapshots.
6. **Permission-Based RBAC** — Granular permission checks (`student.read`, `counselling.create`, `attendance.correction.approve`) rather than rigid role strings.
7. **Event-Driven Internal Architecture** — Decoupled modules publish domain events to an in-process `EventBus` consumed by Timeline, Notification, Risk Engine, and Audit subscribers.
8. **Immutability & Auditability** — Counselling session observations are append-only and cannot be modified or deleted. All models inherit audit metadata (`created_by`, `updated_by`, `version`, `deleted_at`, `archived_at`).
9. **Multi-Tier Logging** — 6 distinct log streams: Application Logs, Audit Logs, Auth Logs, Security Logs, API Logs, and Background Task Logs.
10. **Structured 12-Section Settings Architecture** — Profile, Appearance, Notifications, Security, Institution, Academic, Departments, Users, Storage, Audit, Integrations, and System Flags.

---

## 📁 Monorepo Directory Structure

```
c:\student counsellor\
├── apps/
│   ├── frontend/                     # React 19 + TypeScript + Vite + Tailwind CSS v4
│   │   ├── public/
│   │   ├── src/
│   │   │   ├── app/                  # App shell, router, providers
│   │   │   ├── features/             # Feature-based domain modules
│   │   │   │   ├── auth/             # Login, ForgotPassword, ResetPassword
│   │   │   │   ├── admin/            # AcademicConfig (Departments, Subjects, Years)
│   │   │   │   ├── students/         # Student 360° Workspace
│   │   │   │   ├── counselling/      # Sessions, Follow-ups, New Session
│   │   │   │   ├── attendance/       # 3-Click Record Attendance
│   │   │   │   ├── academics/        # Marks Entry & Backlogs
│   │   │   │   ├── parents/          # Parent Communication Logs
│   │   │   │   ├── notifications/    # Notification Center
│   │   │   │   ├── reports/          # Reports Catalog & Generator
│   │   │   │   ├── settings/         # 12-Section Settings Architecture
│   │   │   │   └── audit/            # Multi-Tier Audit Log Viewer
│   │   │   ├── shared/               # Shared UI design system & primitives
│   │   │   │   ├── components/
│   │   │   │   │   ├── ui/           # Button, Badge, Card, Input, Skeleton, Spinner, EmptyState, StatCard, Timeline, PageHeader, Breadcrumbs, Pagination
│   │   │   │   │   └── layout/       # AppShell, AppHeader, Sidebar
│   │   │   │   ├── lib/              # Axios instance, TanStack Query client
│   │   │   │   └── utils/            # cn class merger
│   │   │   ├── styles/               # Global CSS & design tokens
│   │   │   └── main.tsx
│   │   ├── index.html
│   │   ├── vite.config.ts
│   │   └── tsconfig.json
│   │
│   └── backend/                      # FastAPI Python Application
│       ├── app/
│       │   ├── main.py               # FastAPI application factory
│       │   ├── config.py             # Pydantic BaseSettings
│       │   ├── database.py           # Async SQLAlchemy 2.0 engine & session pool
│       │   ├── dependencies.py       # Auth & database dependencies
│       │   ├── core/
│       │   │   ├── enums.py          # Unified core Backend Enums module
│       │   │   ├── security.py       # JWT & bcrypt password hashing
│       │   │   ├── permissions.py    # Permission-based RBAC checker
│       │   │   ├── exceptions.py     # AppException hierarchy
│       │   │   ├── events.py         # Domain Event Bus
│       │   │   ├── pagination.py     # Pagination utilities
│       │   │   └── feature_flags.py  # Feature flag service
│       │   ├── middleware/
│       │   │   ├── cors.py           # CORS middleware
│       │   │   ├── request_id.py     # X-Request-ID header tracer
│       │   │   ├── rate_limit.py     # Sliding window rate limiter
│       │   │   └── error_handler.py  # Global Error Envelope handler
│       │   ├── api/v1/
│       │   │   └── health.py         # Liveness, Readiness, Startup probes
│       │   ├── features/             # Feature domain modules
│       │   │   ├── auth/             # User, Role, Permission, JWT Tokens
│       │   │   ├── admin/            # Department, Section, AcademicYear, Subject
│       │   │   ├── students/         # Student 360° aggregator & Risk engine
│       │   │   ├── counselling/      # CounsellingSession (immutable) & ActionItems
│       │   │   ├── attendance/       # AttendanceRecord & Correction workflow
│       │   │   ├── academics/        # Mark, SGPAHistory, Backlog
│       │   │   ├── parents/          # ParentCommunication logs
│       │   │   ├── notifications/    # Notification Center & events
│       │   │   ├── reports/          # ReportRecord generator & export
│       │   │   └── audit/            # AuditLog & SystemSetting
│       │   └── shared/
│       │       ├── models/base.py    # AuditMixin, SoftDeleteMixin, Versioning
│       │       └── utils/idempotency.py # Idempotency key cache
│       ├── alembic/                  # Database migration scripts
│       ├── tests/                    # Unit and integration tests
│       ├── requirements.txt
│       └── alembic.ini
│
├── packages/
│   └── types/                        # Shared TypeScript + Python Enums & Interfaces
│       ├── src/
│       │   ├── enums.ts              # All standardized enums
│       │   ├── common.ts             # Pagination, ApiError, AuditMetadata
│       │   └── index.ts
│       └── package.json
│
├── docs/                             # Architecture specs & Developer guide
│   ├── Architecture.md
│   └── Contributing.md
├── docker/                           # Docker Compose & Dockerfiles
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── .env.example
├── README.md
└── package.json                      # Monorepo root package.json
```

---

## 🛠️ Technology Stack

### Frontend Architecture
- **Framework:** React 19 + TypeScript + Vite
- **Styling:** Tailwind CSS v4 + custom CSS variables
- **Primitives:** shadcn/ui (Radix UI base)
- **Data Fetching:** TanStack Query (React Query v5)
- **Routing:** React Router v6
- **Forms & Validation:** React Hook Form + Zod
- **Icons:** Lucide React

### Backend Architecture
- **Framework:** FastAPI 0.110+ (Python 3.12)
- **ORM & Database:** Async SQLAlchemy 2.0 + asyncpg + PostgreSQL 16+
- **Migrations:** Alembic
- **Validation:** Pydantic v2 & Pydantic-Settings
- **Security:** Python-Jose (JWT), Passlib + Bcrypt (Cost factor 12)
- **Logging & Events:** In-process EventBus, structured JSON loggers

---

## 🚀 Build & Run Commands

```bash
# 1. Build Types Package
npm run build --workspace=@scms/types

# 2. Build Frontend App (TypeScript + Vite)
npm run build --workspace=scms-frontend

# 3. Test Backend Python Imports & Startup
python -c "import app.main; print('Backend loaded successfully!')"
```

---

## 🌐 API Endpoint Reference

| Domain | Method | Endpoint | Description | Permission |
|---|---|---|---|---|
| **Health** | GET | `/api/v1/health/live` | Liveness probe | Public |
| | GET | `/api/v1/health/ready` | Readiness probe (DB & Disk) | Public |
| | GET | `/api/v1/health/startup` | Startup probe | Public |
| **Auth** | POST | `/api/v1/auth/login` | Login, returns JWT + sets cookie | Public |
| | POST | `/api/v1/auth/refresh` | Refresh access token | Refresh Cookie |
| | POST | `/api/v1/auth/logout` | Revoke token family & clear cookie | Authenticated |
| | GET | `/api/v1/auth/me` | Current profile & permissions | Authenticated |
| | POST | `/api/v1/auth/forgot-password` | Initiate password reset | Public |
| | POST | `/api/v1/auth/reset-password` | Complete password reset | Public |
| **Admin** | POST | `/api/v1/admin/departments` | Create department | `department.manage` |
| | GET | `/api/v1/admin/departments` | List departments | Authenticated |
| | POST | `/api/v1/admin/subjects` | Create subject | `subject.manage` |
| | GET | `/api/v1/admin/subjects` | List subjects | Authenticated |
| | POST | `/api/v1/admin/users` | Create user account | `user.manage` |
| **Students** | GET | `/api/v1/students/{id}/workspace` | Get 360° workspace data | `student.read` |
| | GET | `/api/v1/students/{id}` | Get student profile | `student.read` |
| | PATCH | `/api/v1/students/{id}/risk` | Update risk flag + emit event | `student.risk.update` |
| **Counselling** | POST | `/api/v1/counselling/sessions` | Create immutable session (≥50 chars) | `counselling.create` |
| | GET | `/api/v1/counselling/sessions` | List sessions | `counselling.read` |
| | GET | `/api/v1/counselling/follow-ups` | List action item follow-ups | `counselling.read` |
| | POST | `/api/v1/counselling/sessions/{id}/acknowledge` | Student session acknowledgment | `counselling.acknowledge` |
| **Attendance** | POST | `/api/v1/attendance` | Bulk 3-click attendance record | `attendance.create` |
| | GET | `/api/v1/attendance/student/{id}` | Student attendance summary | `attendance.read` |
| | POST | `/api/v1/attendance/corrections` | Request attendance correction | `attendance.correction.create` |
| | PATCH | `/api/v1/attendance/corrections/{id}` | Approve/reject correction | `attendance.correction.approve` |
| **Academics** | POST | `/api/v1/marks` | Record bulk marks with max validation | `marks.create` |
| | GET | `/api/v1/academics/student/{id}/backlogs` | Student backlog list | `academics.read` |
| | POST | `/api/v1/academics/student/{id}/gpa/calculate` | Compute SGPA/CGPA | `academics.read` |
| **Parents** | POST | `/api/v1/parent-communication` | Log parent interaction | `parent_communication.create` |
| | GET | `/api/v1/parent-communication/student/{id}` | Student parent call history | `parent_communication.read` |
| **Notifications** | GET | `/api/v1/notifications` | List user notifications | Authenticated |
| | GET | `/api/v1/notifications/unread-count` | Get unread count badge | Authenticated |
| | PATCH | `/api/v1/notifications/{id}/read` | Mark single notification read | Authenticated |
| | PATCH | `/api/v1/notifications/read-all` | Mark all notifications read | Authenticated |
| **Reports** | POST | `/api/v1/reports/generate` | Generate PDF/Excel/CSV report | `report.generate` |
| | GET | `/api/v1/reports/history` | List generated reports | `report.download` |
| **Audit & Settings** | GET | `/api/v1/admin/audit-logs` | Query multi-tier audit logs | `audit.read` |
| | GET | `/api/v1/settings/{section}` | Get 12-section config | `settings.manage` |
| | PUT | `/api/v1/settings/{section}/{key}` | Update system setting | `settings.manage` |

---

## 📝 Changelog

### 2026-07-21

**Fixed:**
- Fixed npm workspace protocol issue in `apps/frontend/package.json` (`@scms/types: "*"`).
- Resolved `@hookform/resolvers` dependency missing error in frontend build.
- Fixed TypeScript compilation errors across all frontend feature pages (`auth.service.ts`, `attendance.service.ts`, `AuditLogsPage.tsx`, `NewSessionPage.tsx`, `LoginPage.tsx`, `MarksEntryPage.tsx`, `AcademicConfigPage.tsx`, `RecordAttendancePage.tsx`, `ParentCommunicationPage.tsx`, `AppHeader.tsx`, `router.tsx`).
- Created unified core backend enums module (`app/core/enums.py`) resolving Python package import path issues.
- Fixed `NameError: name 'Optional'` in `app/core/events.py` and `app/features/auth/service.py`.
- Added missing exception aliases (`UnauthorizedError`, `RateLimitError`) in `app/core/exceptions.py`.
- Added missing security aliases (`hash_password`, `decode_jwt_token`) in `app/core/security.py`.
- Fixed missing SQLAlchemy `DateTime` import in `app/features/students/models.py`.

---

## 🔒 Security & Defense-in-Depth

- **Token Storage:** Access tokens in memory, Refresh tokens in `HttpOnly`, `SameSite=Lax`, `Secure` cookies.
- **Refresh Token Family Rotation:** Theft detection with automatic family revocation.
- **Session Immutability:** Counselling observations are append-only.
- **Rate Limiting:** Sliding window rate limiting applied globally and strictly on `/auth/login`.

---

## 📄 License & Attribution

Internal Enterprise Platform — All rights reserved.
