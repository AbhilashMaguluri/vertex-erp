# Environment Variables Reference & Configuration

This document documents every environment variable supported by the application via `apps/backend/app/config.py` (`pydantic-settings`).

---

## 1. Environment File Location

The backend always resolves its environment configuration from `apps/backend/.env` regardless of the process's working directory.

Template file location: [`apps/backend/.env.example`](file:///c:/vertex-erp/apps/backend/.env.example)

---

## 2. Complete Environment Variables Table

| Variable Name | Type | Required | Default Value | Description |
| :--- | :--- | :---: | :--- | :--- |
| `ENVIRONMENT` | String | No | `development` | Operating environment (`development`, `staging`, `production`). |
| `PROJECT_NAME` | String | No | `Student Counselling Management System` | Institutional application title displayed in API docs. |
| `API_V1_STR` | String | No | `/api/v1` | URL prefix for version 1 REST endpoints. |
| `LOG_LEVEL` | String | No | `INFO` | System logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `DATABASE_URL` | String | **Yes** | *None* | PostgreSQL connection URL (`postgresql+asyncpg://user:pass@host:5432/dbname?ssl=require`). |
| `JWT_SECRET_KEY` | String | **Yes** | *None* | 64-character secret key for cryptographic JWT signing. |
| `JWT_ALGORITHM` | String | No | `HS256` | Cryptographic algorithm for signing JWT access tokens. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | No | `15` | Expiration time for access tokens in minutes. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Integer | No | `1` | Default refresh token cookie validity in days. |
| `REMEMBER_ME_REFRESH_TOKEN_EXPIRE_DAYS` | Integer | No | `30` | Refresh token cookie validity when "Remember Me" is checked. |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`| Integer | No | `30` | Expiration time for password reset tokens in minutes. |
| `COOKIE_SECURE` | Boolean | No | `false` | Enforces HTTPS-only cookies (automatically forced `true` outside `development`). |
| `COOKIE_SAMESITE` | String | No | `lax` | Cookie SameSite transport policy (`lax`, `strict`, `none`). |
| `COOKIE_DOMAIN` | String | No | `None` | Domain scope for refresh token cookie. |
| `BACKEND_CORS_ORIGINS` | String | No | `http://localhost:5173,http://localhost:3000` | Comma-separated list of allowed CORS origins. |
| `MAX_FILE_SIZE_MB` | Integer | No | `10` | Maximum file upload size limit in megabytes. |
| `CLOUDINARY_CLOUD_NAME` | String | **Yes** | *None* | Cloudinary cloud account name for file storage. |
| `CLOUDINARY_API_KEY` | String | **Yes** | *None* | Cloudinary API access key. |
| `CLOUDINARY_API_SECRET` | String | **Yes** | *None* | Cloudinary API secret key. |
| `RESEND_API_KEY` | String | **Yes** | *None* | Resend API key for sending emails. |
| `EMAIL_FROM` | String | **Yes** | *None* | Verified sender email address (e.g. `notifications@college.edu`). |
| `INITIAL_ADMIN_EMAIL` | String | No | `admin@scms.local` | Email address used by seed script for initial admin creation. |
| `INITIAL_ADMIN_PASSWORD` | String | No | `ChangeMe123!` | Temporary password used by seed script. |
| `INITIAL_ADMIN_FIRST_NAME` | String | No | `System` | First name of bootstrap admin user. |
| `INITIAL_ADMIN_LAST_NAME` | String | No | `Administrator` | Last name of bootstrap admin user. |
| `GROQ_API_KEY` | String | No | `""` | Groq API key for Vertex AI streaming LLM integration. |
| `LLM_PROVIDER` | String | No | `groq` | Provider for Vertex AI engine. |
| `LLM_MODEL` | String | No | `llama-3.1-8b-instant` | Model identifier for Vertex AI engine. |

---

## 3. Configuration Validation & Fail-Fast Behavior

If any required variable (`DATABASE_URL`, `JWT_SECRET_KEY`, `CLOUDINARY_*`, `RESEND_API_KEY`, `EMAIL_FROM`) is missing during backend startup, `apps/backend/app/config.py` outputs a stderr diagnostic message and terminates with exit code 1.
