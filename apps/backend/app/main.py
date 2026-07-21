import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.core.exceptions import AppException
from app.middleware.cors import setup_cors
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.error_handler import (
    app_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.api.v1.health import router as health_router
from app.features.auth.router import router as auth_router
from app.features.admin.router import router as admin_router
from app.features.students.router import router as students_router
from app.features.counselling.router import router as counselling_router
from app.features.attendance.router import router as attendance_router
from app.features.academics.router import router as academics_router
from app.features.parents.router import router as parents_router
from app.features.notifications.router import router as notifications_router
from app.features.reports.router import router as reports_router
from app.features.audit.router import router as audit_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} backend in {settings.ENVIRONMENT} mode...")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME} backend...")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="2.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # Middleware
    setup_cors(app)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Error Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Routers
    app.include_router(health_router, prefix=settings.API_V1_STR)
    app.include_router(auth_router, prefix=settings.API_V1_STR)
    app.include_router(admin_router, prefix=settings.API_V1_STR)
    app.include_router(students_router, prefix=settings.API_V1_STR)
    app.include_router(counselling_router, prefix=settings.API_V1_STR)
    app.include_router(attendance_router, prefix=settings.API_V1_STR)
    app.include_router(academics_router, prefix=settings.API_V1_STR)
    app.include_router(parents_router, prefix=settings.API_V1_STR)
    app.include_router(notifications_router, prefix=settings.API_V1_STR)
    app.include_router(reports_router, prefix=settings.API_V1_STR)
    app.include_router(audit_router, prefix=settings.API_V1_STR)

    return app


app = create_app()
