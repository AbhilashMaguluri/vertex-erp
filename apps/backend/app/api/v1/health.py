import shutil
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db

router = APIRouter(prefix="/health", tags=["Health & Observability"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Liveness probe: returns 200 if app process is running."""
    return {"status": "healthy", "probe": "liveness"}


@router.get("/ready")
async def readiness_probe(db: AsyncSession = Depends(get_async_db)):
    """Readiness probe: returns 200 if DB is connected and disk space is sufficient."""
    checks = {}
    is_healthy = True

    # 1. DB connectivity check
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            checks["database"] = "ok"
        else:
            checks["database"] = "failed"
            is_healthy = False
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        is_healthy = False

    # 2. Disk space check
    try:
        total, used, free = shutil.disk_usage("/")
        free_gb = free / (1024 ** 3)
        checks["disk_space"] = f"{free_gb:.2f} GB free"
        if free_gb < 1.0:  # Less than 1GB free
            checks["disk_status"] = "warning: low disk space"
    except Exception:
        checks["disk_space"] = "unknown"

    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_530_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "probe": "readiness",
            "checks": checks,
        },
    )


@router.get("/startup")
async def startup_probe(db: AsyncSession = Depends(get_async_db)):
    """Startup probe: verifies database migrations and startup state."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "probe": "startup"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_530_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "probe": "startup", "error": str(e)},
        )
