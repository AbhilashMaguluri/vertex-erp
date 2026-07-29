import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request_id,
                "details": exc.details if exc.details else None,
            }
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    details = []
    for err in exc.errors():
        # Dot-joined so it lines up 1:1 with a react-hook-form field path
        # (e.g. "student_details.roll_number") for client-side error mapping.
        field_path = ".".join([str(p) for p in err.get("loc", []) if p != "body"])
        details.append({
            "field": field_path,
            "code": err.get("type", "INVALID"),
            "message": err.get("msg", "Validation error"),
        })

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The provided request data is invalid",
                "request_id": request_id,
                "details": details,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path} (request_id={request_id}): {str(exc)}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Our team has been notified.",
                "request_id": request_id,
            }
        },
    )
