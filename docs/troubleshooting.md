# Troubleshooting & Diagnostic Guide

This document provides diagnostic steps and solutions for common setup issues, configuration errors, and runtime failures.

---

## 1. Diagnostic Commands

Use these commands to verify system state:

```bash
# 1. Test Backend Configuration & Database Connection
cd apps/backend
python -c "from app.config import settings; print('Config OK:', settings.PROJECT_NAME)"

# 2. Check Database Migration Status
alembic current
alembic heads

# 3. Test Liveness & Readiness Probes
curl http://localhost:8000/api/v1/health/live
curl http://localhost:8000/api/v1/health/ready
```

---

## 2. Common Issues & Solutions

### Issue 1: Backend Fails to Start (`SCMS backend configuration is incomplete`)

**Symptom**:
```
======================================================================
SCMS backend configuration is incomplete.
Expected an .env file at: c:\vertex-erp\apps\backend\.env
Missing required variable(s): DATABASE_URL, JWT_SECRET_KEY, ...
======================================================================
```

**Solution**:
- Ensure `.env` exists in `apps/backend/` (not in the monorepo root).
- Copy `apps/backend/.env.example` to `apps/backend/.env` and fill in all mandatory variables (`DATABASE_URL`, `JWT_SECRET_KEY`, `CLOUDINARY_*`, `RESEND_API_KEY`, `EMAIL_FROM`).

---

### Issue 2: `HTTP 403 Forbidden` (`PASSWORD_CHANGE_REQUIRED`)

**Symptom**:
API calls return `HTTP 403 Forbidden` with error details:
```json
{
  "detail": "PASSWORD_CHANGE_REQUIRED"
}
```

**Solution**:
Newly created accounts (including the initial admin created via `python -m app.scripts.seed`) start with `force_password_change = true`. Log in and change the password via `POST /api/v1/auth/change-password`.

---

### Issue 3: Migration Version Mismatch (`alembic.util.exc.CommandError`)

**Symptom**:
```
alembic.util.exc.CommandError: Target database is not up to date.
```

**Solution**:
Apply missing Alembic migrations:
```bash
cd apps/backend
alembic upgrade head
```

---

### Issue 4: CORS Errors on Frontend Requests

**Symptom**:
Browser console shows: `Access to XMLHttpRequest at 'http://localhost:8000/...' from origin 'http://localhost:5173' has been blocked by CORS policy`.

**Solution**:
Ensure your frontend development origin (`http://localhost:5173`) is listed in `BACKEND_CORS_ORIGINS` inside `apps/backend/.env`:
```env
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```
Restart the Uvicorn server after updating `.env`.
