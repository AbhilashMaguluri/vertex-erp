# Student Counselling Management System (SCMS) — Enterprise ERP

<p align="center">
  <img src="https://raw.githubusercontent.com/shadcn/ui/main/apps/www/public/og.png" alt="SCMS Banner" width="100%" />
</p>

<p align="center">
  <b>An Institutional SaaS ERP & Student Relationship Management (SRM) Platform</b><br/>
  <i>Engineered with Clean Architecture, FastAPI 0.110, React 19, Vite, and PostgreSQL 16.</i>
</p>

<p align="center">
  <a href="#-documentation-hub"><img src="https://img.shields.io/badge/Documentation-Complete-009688.svg?style=flat-square&logo=readme&logoColor=white" alt="Documentation" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License" /></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="Python" /></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.110-009688.svg?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" /></a>
  <a href="https://react.dev"><img src="https://img.shields.io/badge/React-19.0-61DAFB.svg?style=flat-square&logo=react&logoColor=white" alt="React" /></a>
  <a href="https://vitejs.dev"><img src="https://img.shields.io/badge/Vite-5.2-646CFF.svg?style=flat-square&logo=vite&logoColor=white" alt="Vite" /></a>
  <a href="https://www.postgresql.org"><img src="https://img.shields.io/badge/PostgreSQL-16.0-4169E1.svg?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL" /></a>
  <a href="https://www.docker.com"><img src="https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat-square&logo=docker&logoColor=white" alt="Docker" /></a>
</p>

---

## 📌 Quick Links

- [🚀 Quick Start Guide](#-quick-start)
- [📖 Documentation Hub](#-documentation-hub)
- [🏢 System Architecture](#-architecture-overview)
- [🛠️ Tech Stack](#%EF%B8%8F-technology-stack)
- [🤝 Contributing Guidelines](docs/contributing.md)

---

## 💡 Project Overview

### Problem Statement
Higher education institutions routinely manage student mentorship, academic counselling, attendance defaulters, and placement readiness using physical paper registers and unencrypted spreadsheets. This leads to lost historical notes during counsellor changes, delayed interventions for at-risk students, and significant compliance deficits during institutional accreditation audits.

### Enterprise Solution
SCMS is a closed institutional SaaS platform built around Clean Architecture, Event-Driven Domain Notifications, and Role-Based Access Control (RBAC). It unifies Students, Counsellors, Department Heads (HODs), Faculty, and Administrators into role-specific workspaces:

- **Student 360° Workspace**: Consolidated profile combining academic history, attendance metrics, counselling summaries, document vaults, and placement milestones.
- **Counsellor Caseload Hub**: High-touch workspace featuring risk-level indicators, session scheduling, follow-up trackers, and pre-meeting AI briefings.
- **Reach Out (SRM) Hub**: Multi-counsellor department topology, student appointment booking, campus emergency hotlines, and real-time communication timeline logging.
- **Office Import Engine**: Automated 5-step Excel/CSV ingestion pipeline that parses college spreadsheets, validates roll numbers, creates accounts, issues credentials, and exports PDF audit reports.
- **Vertex AI Engine**: Integrated Server-Sent Events (SSE) streaming assistant providing real-time guidance, pre-meeting briefings, and dynamic UI action triggers.

---

## ✨ Feature Highlights

| Domain | Key Capabilities | Detailed Docs |
| :--- | :--- | :--- |
| **🎓 Student 360** | Academic transcripts, SGPA/CGPA calculations, backlog tracking, self-service profile management, document vault, and academic correction workspace. | [`docs/architecture.md`](docs/architecture.md) |
| **👨‍🏫 Counsellor Desk** | Caseload filtering, attention-required dashboard, append-only session logging, confidential notes, follow-up tracker, and SRM timeline logging. | [`docs/authentication.md`](docs/authentication.md) |
| **🏢 HOD Supervision** | Department-wide counsellor caseload monitoring, attendance compliance stats, and section academic breakdown. | [`docs/architecture.md`](docs/architecture.md) |
| **🛠️ Admin Workspace** | Department & academic year hierarchy configuration, user provisioning, session revocation, office import wizard, and audit log viewer. | [`docs/security.md`](docs/security.md) |
| **🤖 Vertex AI Engine** | SSE streaming LLM assistant (`/api/vertex/message`), Groq / Llama 3.1 provider, student pre-meeting summaries, and dynamic UI action triggers. | [`docs/api.md`](docs/api.md) |
| **📥 Office Import** | 5-step spreadsheet ingestion pipeline (Analyze → Preview → Configure → Execute → Export Credentials & PDF Audit Reports). | [`docs/api.md`](docs/api.md) |
| **📞 Reach Out (SRM)** | Department multi-counsellor assignments, student appointment booking, emergency contact hotlines, and channel policy controls. | [`docs/database.md`](docs/database.md) |

---

## 🖼️ Application Screenshot Gallery

<div align="center">
  <table>
    <tr>
      <td width="50%">
        <img src="https://raw.githubusercontent.com/shadcn/ui/main/apps/www/public/og.png" alt="Student 360 Workspace" /><br/>
        <b>Student 360 Workspace</b> — <i>Unified academic, attendance, and milestone profile.</i>
      </td>
      <td width="50%">
        <img src="https://raw.githubusercontent.com/shadcn/ui/main/apps/www/public/og.png" alt="Counsellor Workspace" /><br/>
        <b>Counsellor Caseload Desk</b> — <i>Attention required, risk levels, and follow-ups.</i>
      </td>
    </tr>
    <tr>
      <td width="50%">
        <img src="https://raw.githubusercontent.com/shadcn/ui/main/apps/www/public/og.png" alt="Reach Out SRM Hub" /><br/>
        <b>Reach Out (SRM) Hub</b> — <i>Counsellor persona profiles and emergency hotlines.</i>
      </td>
      <td width="50%">
        <img src="https://raw.githubusercontent.com/shadcn/ui/main/apps/www/public/og.png" alt="Office Import Engine" /><br/>
        <b>Office Import Engine</b> — <i>5-step spreadsheet parser & credential generator.</i>
      </td>
    </tr>
  </table>
</div>

---

## 🏢 Architecture Overview

SCMS is structured into Clean Architecture domain layers across a workspace-oriented monorepo:

```mermaid
graph TB
    subgraph Client Layer
        Web["React 19 + TypeScript + Vite<br/>(Tailwind CSS v4 + TanStack Query)"]
    end

    subgraph Gateway Layer
        FastAPI["FastAPI 0.110 Gateway"]
        Middleware["Middleware Chain<br/>(RequestId -> RateLimit -> CORS -> Auth/RBAC)"]
    end

    subgraph Service & Storage Layer
        Services["Domain Services<br/>(Auth, Admin, Student 360, Counselling, SRM, Import, Vertex AI)"]
        PostgreSQL[("PostgreSQL 16 Database<br/>(SQLAlchemy 2.0 Async + Alembic)")]
        Cloudinary["Cloudinary API (Storage)"]
        Resend["Resend API (Email)"]
        Groq["Groq API (Llama 3.1 LLM)"]
    end

    Web -->|HTTP / REST / SSE| FastAPI
    FastAPI --> Middleware
    Middleware --> Services
    Services --> PostgreSQL
    Services --> Cloudinary
    Services --> Resend
    Services --> Groq
```

*For complete clean architecture specifications, event bus pub/sub designs, and request lifecycle flowcharts, see [`docs/architecture.md`](docs/architecture.md).*

---

## 🛠️ Technology Stack

| Component | Framework / Library | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend** | React, TypeScript, Vite | `19.0` / `5.4` / `5.2` | Single-page client web application |
| **Styling** | Tailwind CSS v4, Radix UI | `4.0` / Headless | Accessible UI primitives & design tokens |
| **State & Forms** | TanStack Query, React Hook Form | `5.28` / `7.51` | Server cache state & Zod validated forms |
| **Backend API** | FastAPI, Uvicorn | `0.110` / `0.28` | Asynchronous REST & SSE Gateway |
| **Database** | PostgreSQL, SQLAlchemy, asyncpg | `16.0` / `2.0` / `0.29` | Async ORM mapping & connection pool |
| **Migrations** | Alembic | `1.13` | Database schema migrations (12 revisions) |
| **AI Engine** | Groq SDK (Llama-3.1-8b-instant) | `0.9.0` | Vertex AI token streaming & agent tools |
| **External APIs** | Cloudinary, Resend | `1.36` / `2.0` | Cloud document storage & email delivery |
| **Containers** | Docker, Docker Compose | Multi-Stage | Production containerized deployment |

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** `v20+` & **npm** `v10+`
- **Python** `3.12+`
- **PostgreSQL** `16+`

### 5-Minute Setup

1. **Clone Monorepo & Install Node Dependencies**:
   ```bash
   git clone https://github.com/your-org/vertex-erp.git
   cd vertex-erp
   npm install
   ```

2. **Configure Backend Environment**:
   ```bash
   cd apps/backend
   python -m venv venv

   # Activate virtual environment:
   source venv/bin/activate        # Linux / macOS
   .\venv\Scripts\Activate.ps1     # Windows PowerShell

   pip install -r requirements.txt
   cp .env.example .env
   ```
   *Edit `apps/backend/.env` and set mandatory keys (`DATABASE_URL`, `JWT_SECRET_KEY`, `CLOUDINARY_*`, `RESEND_API_KEY`, `EMAIL_FROM`).*

3. **Run Migrations & Seed Bootstrap Admin**:
   ```bash
   alembic upgrade head
   python -m app.scripts.seed
   ```

4. **Launch Local Development Servers**:
   ```bash
   # From project root directory:
   npm run dev:frontend   # React client at http://localhost:5173
   npm run dev:backend    # FastAPI server at http://localhost:8000
   ```

---

## 📖 Documentation Hub

For detailed technical specifications, refer to our modular documentation suite under [`/docs`](docs/):

- 📐 **[System Architecture](docs/architecture.md)** — Topology, Clean Architecture layers, ER diagrams, and request lifecycles.
- 🔌 **[API Reference](docs/api.md)** — Complete endpoint reference for all 158 HTTP REST and SSE routes.
- 🗄️ **[Database & Migrations](docs/database.md)** — Documentation of 48 database models and 12 Alembic migrations.
- 🔐 **[Authentication & Authorization](docs/authentication.md)** — User hierarchy, token rotation, and full RBAC permission matrix.
- ⚙️ **[Environment Variables](docs/environment.md)** — Exhaustive configuration reference table for `.env` settings.
- 📁 **[Project Structure](docs/project-structure.md)** — Line-by-line annotated monorepo file map.
- 💻 **[Development Guide](docs/development.md)** — Onboarding rules, coding standards, and guide for adding feature modules.
- 🐳 **[Production Deployment](docs/deployment.md)** — Docker Compose, Dockerfiles, Nginx SSE buffering, and SSL setup.
- 🛡️ **[Security & Governance](docs/security.md)** — Password hashing, token theft prevention, rate limiting, and audit logs.
- 🔧 **[Troubleshooting & Diagnostics](docs/troubleshooting.md)** — Common setup pitfalls and diagnostic shell commands.
- 🗺️ **[Roadmap & Operational Boundaries](docs/roadmap.md)** — Planned features and explicit system boundaries.
- 🤝 **[Contributing Guidelines](docs/contributing.md)** — 15-point Definition of Done (DoD) & pull request requirements.

---

## 🐳 Production Deployment Overview

Production deployments utilize Docker Compose or containerized Kubernetes pods.

```bash
# Build and launch all services in background
docker-compose -f docker/docker-compose.yml up -d --build
```

For complete Nginx proxy settings (`proxy_buffering off` for SSE), Let's Encrypt SSL instructions, and production checklists, see [`docs/deployment.md`](docs/deployment.md).

---

## 🤝 Contributing

We welcome contributions! Please review our [Developer Contribution Guidelines](docs/contributing.md) to understand our 15-point Definition of Done (DoD) before submitting pull requests.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

<p align="center">
  <b>Student Counselling Management System (SCMS) Enterprise Platform</b><br/>
  <i>Built for Higher Education Institutions.</i>
</p>
