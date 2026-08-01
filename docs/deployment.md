# Production Deployment Guide

This guide documents deployment procedures for the Student Counselling Management System (SCMS), covering the current Render + Vercel production setup, Docker Compose self-hosted deployment, and Nginx reverse proxy configurations.

---

## 1. Current Production: Render (Backend) + Vercel (Frontend)

The live deployment uses a split-hosting model:

| Component | Platform | Details |
| :--- | :--- | :--- |
| **Backend API** | [Render](https://render.com) | Python web service running `uvicorn app.main:app` |
| **Frontend SPA** | [Vercel](https://vercel.com) | Static Vite build with API proxy rewrites |
| **Database** | [Neon](https://neon.tech) | Managed serverless PostgreSQL with SSL |

### 1.1 Backend on Render

1. **Create a Web Service** on Render connected to the GitHub repository.
2. **Root Directory**: `apps/backend`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables** (set in Render dashboard):
   - `ENVIRONMENT=production`
   - `DATABASE_URL=postgresql+asyncpg://<user>:<pass>@<host>/<db>?ssl=require`
   - `JWT_SECRET_KEY=<64-char-random-secret>`
   - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
   - `RESEND_API_KEY`, `EMAIL_FROM`
   - `GROQ_API_KEY` (for Vertex AI)
   - `BACKEND_CORS_ORIGINS=https://your-frontend.vercel.app`
   - `COOKIE_DOMAIN=` (leave blank — Render and Vercel are on different domains; the Vercel proxy makes cookies same-origin)
6. **Post-Deploy**: Run migrations on first deploy:
   ```bash
   cd apps/backend && alembic upgrade head && python -m app.scripts.seed
   ```

### 1.2 Frontend on Vercel

1. **Import the repository** on Vercel.
2. **Root Directory**: `apps/frontend`
3. **Framework Preset**: Vite
4. **Build Command**: `npm run build` (Vercel auto-detects)
5. **Environment Variables**: `VITE_API_URL=` (leave empty — the Vercel proxy handles routing)
6. **API Proxy**: The [`vercel.json`](../apps/frontend/vercel.json) file rewrites `/api/*` requests to the Render backend:
   ```json
   {
     "rewrites": [
       {
         "source": "/api/:path*",
         "destination": "https://vertex-erp-backend.onrender.com/api/:path*"
       },
       {
         "source": "/((?!api/).*)",
         "destination": "/index.html"
       }
     ]
   }
   ```
   This makes all API calls same-origin from the browser's perspective, enabling `HttpOnly` cookie transport for refresh tokens.

### 1.3 Important Notes
- **Render cold starts**: Free-tier Render services spin down after inactivity. The first request after a cold start may take 30–60 seconds.
- **Cookie transport**: Because Vercel proxies `/api/*` to Render, the browser sees cookies as same-origin. `COOKIE_SECURE=true` is forced automatically when `ENVIRONMENT != development`.
- **CORS**: Add your Vercel production URL to `BACKEND_CORS_ORIGINS` on Render.

---

## 2. Docker Compose (Self-Hosted)

The repository provides production-ready container configurations:

- **`docker/Dockerfile.backend`**: Python 3.12-slim container running FastAPI via Uvicorn.
- **`docker/Dockerfile.frontend`**: Multi-stage container building Vite static assets with Node.js 20 and serving them via Nginx Alpine on port 80.
- **`docker/docker-compose.yml`**: Docker Compose file orchestrating PostgreSQL 16, backend API, and frontend web server.

### 2.1 Deploy with Docker Compose

1. **Configure Environment File**:
   Ensure `apps/backend/.env` is fully populated with production values (`DATABASE_URL`, `JWT_SECRET_KEY`, `ENVIRONMENT=production`).

2. **Build and Start Containers**:
   ```bash
   docker-compose -f docker/docker-compose.yml up -d --build
   ```

3. **Verify Service Health**:
   ```bash
   docker-compose -f docker/docker-compose.yml ps
   ```

---

## 3. Nginx Reverse Proxy Configuration

When deploying behind an external Nginx load balancer or reverse proxy, use the following server configuration:

```nginx
server {
    listen 80;
    server_name scms.yourcollege.edu;

    # Force HTTPS redirect
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name scms.yourcollege.edu;

    ssl_certificate /etc/letsencrypt/live/scms.yourcollege.edu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/scms.yourcollege.edu/privkey.pem;

    # Frontend Static Assets
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # REST API Gateway
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Vertex AI Server-Sent Events (SSE) Streaming
    location /api/vertex/message {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Disable proxy buffering for real-time SSE token streaming
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
        proxy_read_timeout 600s;
    }
}
```

---

## 4. Production Release Checklist

Before launching in a production environment:

1. Set `ENVIRONMENT=production`.
2. Generate a 64+ character random secret for `JWT_SECRET_KEY`:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```
3. `COOKIE_SECURE` is automatically forced to `true` when `ENVIRONMENT != development` — no manual override needed.
4. Configure explicit production frontend URLs in `BACKEND_CORS_ORIGINS`.
5. Execute database migrations:
   ```bash
   alembic upgrade head
   ```
6. Bootstrap default system roles and admin account:
   ```bash
   python -m app.scripts.seed
   ```
7. For self-hosted: configure SSL/TLS certificates (e.g. Let's Encrypt / Certbot).
8. Verify health endpoints:
   ```bash
   curl https://your-backend-url/api/v1/health/live
   curl https://your-backend-url/api/v1/health/ready
   ```
