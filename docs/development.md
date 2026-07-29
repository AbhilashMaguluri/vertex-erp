# Developer Onboarding & Development Guide

This guide provides developer onboarding instructions, coding standards, automated testing procedures, and step-by-step instructions for implementing new domain feature modules.

---

## 1. Prerequisites & Environment Setup

Ensure the following tools are installed before setting up the workspace:

- **Node.js**: `v20.0.0` or higher
- **npm**: `v10.0.0` or higher
- **Python**: `3.12` or higher
- **PostgreSQL**: `v16.0` or higher (or a Neon PostgreSQL database instance)

### Local Development Setup

1. **Install Root Node Dependencies**:
   ```bash
   npm install
   ```

2. **Configure Python Virtual Environment**:
   ```bash
   cd apps/backend
   python -m venv venv

   # Linux / macOS:
   source venv/bin/activate

   # Windows (PowerShell):
   .\venv\Scripts\Activate.ps1

   pip install -r requirements.txt
   ```

3. **Configure Environment File**:
   Copy `.env.example` to `.env` inside `apps/backend/`:
   ```bash
   cp .env.example .env
   ```
   Fill in mandatory settings (`DATABASE_URL`, `JWT_SECRET_KEY`, `CLOUDINARY_*`, `RESEND_API_KEY`, `EMAIL_FROM`).

4. **Apply Migrations & Seed Bootstrap Admin**:
   ```bash
   alembic upgrade head
   python -m app.scripts.seed
   ```

5. **Launch Local Servers**:
   ```bash
   # From root directory:
   npm run dev:frontend   # Starts Vite server at http://localhost:5173
   npm run dev:backend    # Starts Uvicorn server at http://localhost:8000
   ```

---

## 2. Coding Conventions & Standards

### Python & Backend Standards
- **PEP 8 Compliance**: Enforce 4-space indentation and clean import ordering (standard library → third-party → internal modules).
- **Type Annotations**: Mandatory type hints for all function arguments and return values.
- **Async Operations**: All database queries must be asynchronous (`await db.execute(...)`). Avoid blocking I/O calls on main event loops.
- **Pydantic Validation**: Input validation must use Pydantic v2 models. Handcrafted payload parsing is prohibited.

### TypeScript & React Standards
- **Strict Mode**: Enforce TypeScript strict mode (`"strict": true`). Avoid `any` types.
- **React 19 Hooks**: Use idiomatic React hooks. Server fetches must use TanStack Query (`useQuery`, `useMutation`).
- **Styling**: Component styling must use Tailwind CSS utility classes matching system design tokens.

---

## 3. Step-by-Step Guide: Adding a New Domain Module

To add a new domain feature module (e.g. `placement`):

1. **Create Backend Module Folder**:
   Create `apps/backend/app/features/placement/` with standard Clean Architecture files:
   - `models.py`: Define SQLAlchemy entities inheriting from `Base` and mixins.
   - `schemas.py`: Define Pydantic request body and response DTO schemas.
   - `repository.py`: Write database query methods using `AsyncSession`.
   - `service.py`: Implement business logic, permission validations, and audit logs.
   - `router.py`: Define FastAPI endpoints using `require_permission(...)`.

2. **Register Router in Main App**:
   In `apps/backend/app/main.py`:
   ```python
   from app.features.placement.router import router as placement_router
   app.include_router(placement_router, prefix=settings.API_V1_STR)
   ```

3. **Generate & Apply Database Migration**:
   ```bash
   cd apps/backend
   alembic revision --autogenerate -m "add placement module"
   alembic upgrade head
   ```

4. **Create Frontend Feature Directory**:
   Create `apps/frontend/src/features/placement/` containing components, pages, services, and hooks. Register pages in `apps/frontend/src/app/router.tsx` with appropriate route guards (`ProtectedRoute`, `PermissionGuard`).

---

## 4. Running Tests

The test suite uses `pytest` with `pytest-asyncio`:

```bash
cd apps/backend
pytest
```

Run specific test sub-suites:
```bash
# Integration tests
pytest tests/integration/

# Unit tests
pytest tests/unit/
```
