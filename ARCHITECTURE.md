# System Architecture & Technical Specifications — SCMS Enterprise Platform

## 1. Overview & System Domain Map

The **Student Counselling Management System (SCMS)** is architected around Clean Architecture and Domain-Driven Design (DDD) principles.

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                   Client Web Frontend                   │
                    │         React 19 + TypeScript + Vite + Tailwind CSS      │
                    └────────────────────────────┬────────────────────────────┘
                                                 │ HTTP / REST APIs
                                                 ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │                     FastAPI Layer                       │
                    │         Router + Middleware + Pydantic Validation       │
                    └────────────────────────────┬────────────────────────────┘
                                                 │
                          ┌──────────────────────┼──────────────────────┐
                          ▼                      ▼                      ▼
                 ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                 │ Auth & Security │    │   Student 360   │    │  Reach Out Hub  │
                 │   RBAC + JWT    │    │  Academics/Att. │    │ Database SRM    │
                 └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
                          │                      │                      │
                          └──────────────────────┼──────────────────────┘
                                                 │
                                                 ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │               PostgreSQL Database (Async)               │
                    │        SQLAlchemy 2.0 ORM + Alembic Migrations          │
                    └─────────────────────────────────────────────────────────┘
```

---

## 2. Reach Out (Student Relationship Management) Domain Architecture

### 2.1 Multi-Counsellor & Department Assignment Topology
- **Department**: `departments` table maps academic departments.
- **Multiple Counsellors per Department**: Users with `COUNSELLOR` role assigned to a `department_id`.
- **Assigned Students**: Active mappings in `counsellor_assignments` table (`student_id` <-> `counsellor_id`).
- **Dynamic Scope Resolution**:
  - **Student View**: Looked up dynamically via `CounsellorAssignment`. If unassigned, returns `assigned: false` (`"No counsellor has been assigned yet."`).
  - **Counsellor View**: Scope restricted strictly to assigned student caseload.
  - **HOD View**: Supervised access to all counsellors and caseloads within their department.
  - **Admin View**: Universal configuration access across all departments.

### 2.2 Database Audit Logging System (`reach_out_audit_logs`)
- Every administrative profile modification, channel policy update, or emergency contact CRUD operation triggers an immutable record in `reach_out_audit_logs`:
  - `actor_id`: UUID of user performing update.
  - `action`: Audit action string (`UPDATE_COUNSELLOR_PROFILE`, `UPDATE_CHANNEL_POLICY`, `CREATE_EMERGENCY_CONTACT`, `DELETE_EMERGENCY_CONTACT`).
  - `target_type` & `target_id`: Affected model type and record ID.
  - `old_values` & `new_values`: JSONB snapshots of field delta.
  - `created_at`: Timezone-aware timestamp.

### 2.3 Real Analytics Engine & Database Metrics
- **Communication Health Index**: Computed dynamically from `communication_timeline_logs`. Aggregates response times and follow-up compliance %. If zero logs exist, returns `has_data: false` and `insufficient_data_reason: "Insufficient data."`.
- **Parent Engagement Score**: Aggregates parent calls, meetings, and emails. If zero parent interactions exist, returns `has_data: false`.

### 2.4 Strict Input Validation & Error Envelopes
- Pydantic validators on `CounsellorContactProfileUpdate` enforce regex pattern matching on phone numbers (`^\+?[0-9\s\-\(\)]{7,20}$`) and URLs (`http://` or `https://`).
- Rejects invalid inputs with 422 HTTP Unprocessable Entity status.

---

## 3. Database ER Diagram & Table Schemas

```
+-----------------------------------+       +-----------------------------------+
|    counsellor_contact_profiles    |       |      reach_out_audit_logs         |
+-----------------------------------+       +-----------------------------------+
| id (UUID, PK)                     |       | id (UUID, PK)                     |
| counsellor_id (UUID, FK -> users) |       | actor_id (UUID, FK -> users)      |
| designation (VARCHAR)             |       | action (VARCHAR)                  |
| building, floor, cabin_number     |       | target_type, target_id            |
| office_phone, maps_url            |       | old_values (JSONB)                |
| structured_schedule (JSONB)       |       | new_values (JSONB)                |
| office_status (VARCHAR)           |       | created_at (TIMESTAMPTZ)          |
+-----------------------------------+       +-----------------------------------+

+-----------------------------------+       +-----------------------------------+
|     campus_emergency_contacts     |       |     appointment_requests          |
+-----------------------------------+       +-----------------------------------+
| id (UUID, PK)                     |       | id (UUID, PK)                     |
| name, category (VARCHAR)          |       | student_id (UUID, FK)             |
| phone, email, location            |       | counsellor_id (UUID, FK)          |
| is_24_7 (BOOLEAN)                 |       | request_type, status (VARCHAR)    |
+-----------------------------------+       +-----------------------------------+
```
