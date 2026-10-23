"""Standardised HTTP response helpers.

Every Lambda handler returns responses through these helpers
so that all API responses share one consistent shape.
"""

from __future__ import annotations

import json
from typing import Any


def success(body: dict[str, Any], status_code: int = 200) -> dict[str, Any]:
    """Build a successful API Gateway proxy response."""
    return _response(status_code, body)


def created(body: dict[str, Any]) -> dict[str, Any]:
    """Build a 201 Created response."""
    return _response(201, body)


def bad_request(code: str, message: str) -> dict[str, Any]:
    """Build a 400 Bad Request error response."""
    return _error(400, code, message)


def unauthorized(message: str = "Authentication required") -> dict[str, Any]:
    """Build a 401 Unauthorized error response."""
    return _error(401, "UNAUTHORIZED", message)


def forbidden(message: str = "You do not have permission to perform this action") -> dict[str, Any]:
    """Build a 403 Forbidden error response."""
    return _error(403, "FORBIDDEN", message)


def not_found(message: str = "Resource not found") -> dict[str, Any]:
    """Build a 404 Not Found error response."""
    return _error(404, "NOT_FOUND", message)


def conflict(code: str, message: str) -> dict[str, Any]:
    """Build a 409 Conflict error response."""
    return _error(409, code, message)


def internal_error(message: str = "An unexpected error occurred") -> dict[str, Any]:
    """Build a 500 Internal Server Error response."""
    return _error(500, "INTERNAL_ERROR", message)


def _error(status_code: int, code: str, message: str) -> dict[str, Any]:
    """Build an error response with the standard error envelope."""
    return _response(status_code, {"error": {"code": code, "message": message}})


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """Build a raw API Gateway proxy integration response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body, default=str),
    }
