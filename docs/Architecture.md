# SCMS System Architecture Specification — Version 2.0

## Overview

The **Student Counselling Management System (SCMS)** is an enterprise SaaS application engineered to replace physical counselling registers, paperwork, and fragmented spreadsheets across colleges and universities.

SCMS follows Clean Architecture, Event-Driven Architecture, and Permission-Based Role Access Control (RBAC).

---

## Monorepo Layout

```
c:\student counsellor\
├── apps/
│   ├── frontend/                     # React 19 + TypeScript + Vite + Tailwind CSS v4
│   │   ├── src/app/                  # App shell, router, providers
│   │   ├── src/features/             # Feature domain modules (Auth, Admin, Students, Counselling, Attendance, Academics, Parents, Notifications, Reports, Settings, Audit)
│   │   └── src/shared/               # Design system & components
│   └── backend/                      # FastAPI Python Application
│       ├── app/core/                 # Enums, Security, Permissions, Exceptions, EventBus
│       ├── app/middleware/           # CORS, RequestID, RateLimiting, ErrorHandlers
│       ├── app/features/             # Backend domain modules
│       └── app/shared/               # BaseModel mixins (Audit, SoftDelete, Versioning)
├── packages/
│   └── types/                        # Shared @scms/types package (enums, DTO interfaces)
├── docs/                             # System documentation
├── docker/                           # Container deployment configurations
├── README.md                         # Primary documentation & changelog
└── package.json                      # Monorepo root package.json
```

---

## Key Architectural Principles

1. **Workspace-Oriented Mental Model**: Navigation revolves around role-specific workspaces (Student 360°, Counsellor Workspace, HOD Workspace, Admin Workspace).
2. **Actionable Dashboards**: Every dashboard presents Attention Required → Today's Tasks → Recent Activity → Quick Actions → Insights.
3. **Student 360° Workspace**: Unified hub with 9 tabbed modules (Overview, Timeline, Attendance, Academics, Counselling, Parent Calls, Documents, Reports, Analytics).
4. **Historical Data & Universal Timeline**: All key metrics maintain temporal history. 20+ domain event types published to `EventBus` and logged to the timeline.
5. **Permission-Based RBAC**: Permissions are granular strings (`student.read`, `counselling.create`). Roles map to permission sets.
6. **Session Immutability**: Counselling session observations are append-only and cannot be altered or deleted once submitted.
7. **Soft Delete & Auditability**: All business entities utilize `deleted_at` soft-delete flags. Auditability fields (`created_by`, `updated_by`, `version`) are present on all core models.
8. **Multi-Tier Logging**: 6 separate log channels (Application, Audit, Auth, Security, API, Background Tasks).
9. **Structured 12-Section Settings Architecture**: Profile, Appearance, Notifications, Security, Institution, Academic, Departments, Users, Storage, Audit, Integrations, System Flags.
