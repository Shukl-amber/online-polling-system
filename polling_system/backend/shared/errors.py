"""Application-level error types.

Each error carries a stable code and a human-readable message.
Handlers catch these and map them to the correct HTTP status.
"""

from __future__ import annotations


class AppError(Exception):
    """Base application error with a machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ValidationError(AppError):
    """Input failed validation (maps to 400)."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR") -> None:
        super().__init__(code=code, message=message)


class NotFoundError(AppError):
    """Requested resource does not exist (maps to 404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(code="NOT_FOUND", message=message)


class ConflictError(AppError):
    """Action conflicts with the current state (maps to 409)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(code=code, message=message)


class ForbiddenError(AppError):
    """Caller lacks permission for this action (maps to 403)."""

    def __init__(self, message: str = "You do not have permission to perform this action") -> None:
        super().__init__(code="FORBIDDEN", message=message)
