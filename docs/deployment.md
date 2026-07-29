# Production Deployment Guide

This guide documents containerization, Docker Compose orchestration, Nginx reverse proxy configurations, and production deployment procedures for the Student Counselling Management System (SCMS).

---

## 1. Docker Container Overview

The repository provides production-ready container configurations:

- **`docker/Dockerfile.backend`**: Python 3.12-slim container running FastAPI via Uvicorn.
- **`docker/Dockerfile.frontend`**: Multi-stage container building Vite static assets with Node.js 20 and serving them via Nginx Alpine on port 80.
- **`docker/docker-compose.yml`**: Docker Compose file orchestrating PostgreSQL 16, backend API, and frontend web server.

---

## 2. Docker Compose Deployment

To deploy using Docker Compose:

1. **Configure Environment File**:
   Ensure `apps/backend/.env` is fully populated with production values (`DATABASE_URL`, `JWT_SECRET_KEY`, `ENVIRONMENT=production`, `COOKIE_SECURE=true`).

2. **Build and Start Containers**:
   ```bash
   docker-compose -f docker/docker-compose.yml up -d --build
   ```

3. **Verify Service Health**:
   ```bash
   docker-compose -f docker/docker-compose.yml ps
   ```

---

## 3. Production Nginx Reverse Proxy Configuration

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
3. Set `COOKIE_SECURE=true` in `.env`.
4. Configure explicit production frontend URLs in `BACKEND_CORS_ORIGINS`.
5. Execute database migrations:
   ```bash
   alembic upgrade head
   ```
6. Bootstrap default system roles:
   ```bash
   python -m app.scripts.seed
   ```
7. Configure SSL/TLS certificates (e.g. Let's Encrypt / Certbot).
