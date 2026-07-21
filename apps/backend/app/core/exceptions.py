from typing import Any, Dict, Optional
from fastapi import status


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, code="NOT_FOUND", details=details)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="VALIDATION_ERROR", details=details
        )


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED, code="AUTHENTICATION_FAILED", details=details)


class UnauthenticatedError(AuthenticationError):
    pass


class UnauthorizedError(AuthenticationError):
    pass


class ForbiddenError(AppException):
    def __init__(self, message: str = "Access forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", details=details)


class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT, code="CONFLICT", details=details)


class RateLimitExceededError(AppException):
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message, status_code=status.HTTP_429_TOO_MANY_REQUESTS, code="RATE_LIMIT_EXCEEDED", details=details
        )


class RateLimitError(RateLimitExceededError):
    pass
