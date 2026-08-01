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

---

### Issue 5: `ValueError: password cannot be longer than 72 bytes` (passlib + bcrypt)

**Symptom**:
Login returns `500 Internal Server Error` with traceback containing:
```
File ".../passlib/handlers/bcrypt.py", line 655, in _calc_checksum
    hash = _bcrypt.hashpw(secret, config)
ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
```

**Cause**:
`passlib` 1.7.4 (last release 2020) internally uses a >72-byte test password to probe the bcrypt backend for bug detection. `bcrypt >= 5` rejects this with `ValueError` instead of silently truncating.

**Solution**:
This issue has been resolved in v2.2.0. The `passlib` dependency was removed entirely. `app/core/security.py` now uses `bcrypt` directly with explicit 72-byte truncation. Ensure you are on the latest commit and that `passlib` does not appear in `requirements.txt`. If upgrading from an older version:
```bash
pip uninstall passlib
pip install -r requirements.txt
```

---

### Issue 6: Render Backend Returns `502 Bad Gateway` or Takes 30+ Seconds

**Symptom**:
First request after a period of inactivity returns a timeout or `502` error.

**Cause**:
Render free-tier services spin down after 15 minutes of inactivity. The first inbound request triggers a cold start, which includes installing dependencies and booting the Python process.

**Solution**:
- Wait 30–60 seconds for the cold start to complete and retry.
- For production use, upgrade to a paid Render plan to keep the service always-on.
- Alternatively, set up an external health check ping (e.g., UptimeRobot) hitting `/api/v1/health/live` every 10 minutes to keep the service warm.

---

### Issue 7: Stale Code on Render After Local Fix

**Symptom**:
You've fixed a bug locally but the deployed version on Render still shows the old behavior.

**Solution**:
Ensure your changes are committed **and pushed** to the remote branch that Render is tracking:
```bash
git add -A
git commit -m "fix: description"
git push origin main
```
Render auto-deploys on push. Verify the deploy completed in the Render dashboard under "Events".
