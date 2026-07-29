# Monorepo Project Structure & Layout

This document provides a line-by-line annotated overview of the monorepo directory layout.

---

## Workspace Map

```
c:\vertex-erp\
├── apps/
│   ├── backend/                        # FastAPI Asynchronous Python Application
│   │   ├── alembic/                    # Database migration environment
│   │   │   ├── versions/               # 12 Alembic revision scripts
│   │   │   ├── env.py                  # Async Alembic runner
│   │   │   └── script.py.mako          # Migration template
│   │   ├── app/                        # Application Source Package
│   │   │   ├── ai/                     # Vertex AI Engine & Chatbot
│   │   │   │   ├── agents/             # Task subagents & workflows
│   │   │   │   ├── core/               # Vertex core engine & SSE handlers
│   │   │   │   ├── memory/             # Session context & conversation state
│   │   │   │   ├── models/             # AI request/response Pydantic models
│   │   │   │   ├── providers/          # Groq / Llama provider integrations
│   │   │   │   ├── rag/                # Document RAG & context loaders
│   │   │   │   ├── tools/              # Agent database lookup tools
│   │   │   │   └── router.py           # Endpoint: POST /api/vertex/message (SSE)
│   │   │   ├── api/                    # Core API Gateway
│   │   │   │   └── v1/health.py        # Liveness & Readiness health probes
│   │   │   ├── core/                   # System Cross-Cutting Subsystems
│   │   │   │   ├── audit.py            # Audit logging helpers
│   │   │   │   ├── cloudinary_service.py # Image/Document upload service
│   │   │   │   ├── email.py            # Resend email delivery service
│   │   │   │   ├── enums.py            # System domain Enums
│   │   │   │   ├── events.py           # In-process EventBus pub/sub
│   │   │   │   ├── exceptions.py       # Custom application exceptions
│   │   │   │   ├── feature_flags.py    # Dynamic feature toggle evaluation
│   │   │   │   ├── pagination.py       # Standard pagination helpers
│   │   │   │   ├── permissions.py      # RBAC permission checks
│   │   │   │   ├── scoping.py          # Data ownership & assignment verifiers
│   │   │   │   └── security.py         # Password hashing & JWT token utils
│   │   │   ├── features/               # Domain Feature Modules (Clean Architecture)
│   │   │   │   ├── academics/          # Marks entry, SGPA/CGPA, backlogs
│   │   │   │   ├── admin/              # Academic hierarchy & user management
│   │   │   │   ├── attendance/         # Bulk attendance, correction requests
│   │   │   │   ├── audit/              # System audit log & settings endpoints
│   │   │   │   ├── auth/               # Login, refresh tokens, password change
│   │   │   │   ├── counselling/        # Session logging, follow-up tracker
│   │   │   │   ├── imports/            # Office spreadsheet import engine
│   │   │   │   ├── notifications/      # Notification center & read states
│   │   │   │   ├── parents/            # Parent communication logging
│   │   │   │   ├── reach_out/          # Reach Out (SRM) hub & contacts
│   │   │   │   ├── reports/            # PDF/Excel report generator
│   │   │   │   ├── search/             # Global cross-entity search router
│   │   │   │   └── students/           # Student 360 & Self-Service profiles
│   │   │   ├── middleware/             # HTTP Middleware
│   │   │   │   ├── cors.py             # CORS origins setup
│   │   │   │   ├── error_handler.py    # Global exception handlers
│   │   │   │   ├── rate_limit.py       # Rate limiting middleware
│   │   │   │   └── request_id.py       # Request ID tracing middleware
│   │   │   ├── scripts/                # CLI Utilities
│   │   │   │   └── seed.py             # Idempotent DB seeder script
│   │   │   ├── shared/                 # Base Models & Mixins
│   │   │   │   └── models/base.py      # TimestampMixin, SoftDeleteMixin, AuditMixin
│   │   │   ├── config.py               # Pydantic BaseSettings configuration
│   │   │   ├── database.py             # Async Engine & Session pool
│   │   │   ├── dependencies.py         # Global FastAPI dependencies
│   │   │   └── main.py                 # FastAPI Application Factory
│   │   ├── tests/                      # Pytest Test Suite
│   │   │   ├── integration/            # API integration tests
│   │   │   └── unit/                   # Business logic unit tests
│   │   ├── .env.example                # Template for environment variables
│   │   ├── alembic.ini                 # Alembic configuration
│   │   ├── pytest.ini                  # Pytest runner configuration
│   │   └── requirements.txt            # Python dependencies
│   │
│   └── frontend/                       # React 19 Client Application
│       ├── public/                     # Public web assets
│       ├── src/                        # React Source Package
│       │   ├── app/                    # App Shell & Router
│       │   │   ├── App.tsx             # Root component & providers
│       │   │   ├── providers.tsx       # TanStack Query & Context providers
│       │   │   └── router.tsx          # React Router v6 route configuration
│       │   ├── features/               # Client Feature Subtrees
│       │   │   ├── academics/          # Marks entry views
│       │   │   ├── admin/              # Academic config, user management, import
│       │   │   ├── attendance/         # Attendance marking views
│       │   │   ├── audit/              # System audit log viewer
│       │   │   ├── auth/               # Login, forgot password, change pass
│       │   │   ├── counselling/        # Sessions & follow-up tracking
│       │   │   ├── dashboard/          # Role-based actionable dashboards
│       │   │   ├── notifications/      # Notification center UI
│       │   │   ├── parents/            # Parent communication log UI
│       │   │   ├── reach_out/          # Reach Out (SRM) hub views
│       │   │   ├── reports/            # Reports catalog & export view
│       │   │   ├── search/             # Global search overlay component
│       │   │   ├── settings/           # 12-section institutional settings
│       │   │   ├── students/           # Student 360 workspace & profile pages
│       │   │   └── vertex/             # Vertex AI floating assistant UI
│       │   └── shared/                 # Design System & UI Shared Components
│       │       ├── components/         # Radix UI primitives & Layout
│       │       ├── lib/                # Axios instance & React Query client
│       │       ├── theme/              # Theme tokens & CSS variables
│       │       └── utils/              # Formatter helpers & format validators
│       ├── index.html                  # HTML5 entry point
│       ├── package.json                # Frontend package manifest
│       ├── tsconfig.json               # TypeScript configuration
│       └── vite.config.ts              # Vite build setup
│
├── docker/                             # Deployment Configurations
│   ├── Dockerfile.backend              # Python 3.12 Backend container
│   ├── Dockerfile.frontend             # Multi-stage Node/Nginx Frontend container
│   └── docker-compose.yml              # Local container orchestration
│
├── docs/                               # Documentation Suite
│   ├── architecture.md                 # System topology & Clean Architecture
│   ├── api.md                          # 158 API endpoints reference
│   ├── database.md                     # 48 Database models & 12 migrations
│   ├── authentication.md               # Auth flow, JWT, & RBAC matrix
│   ├── environment.md                  # Environment variables table
│   ├── project-structure.md            # Monorepo directory map
│   ├── development.md                  # Onboarding & module guide
│   ├── deployment.md                   # Production Docker & Nginx guide
│   ├── security.md                     # Security & audit policies
│   ├── troubleshooting.md              # Common issues & diagnostic shell commands
│   ├── roadmap.md                      # Roadmap & operational boundaries
│   └── contributing.md                 # DoD & pull request workflow
│
├── packages/                           # Monorepo Shared Packages
│   └── types/                          # Shared @scms/types package
│       ├── src/
│       │   ├── common.ts               # Interface definitions
│       │   ├── enums.ts                # Shared Enums
│       │   └── index.ts                # Barrel export
│       └── package.json                # Package manifest
│
├── package.json                        # Monorepo root workspace script runner
└── README.md                           # Main Project Entry Point & Hero Page
```
