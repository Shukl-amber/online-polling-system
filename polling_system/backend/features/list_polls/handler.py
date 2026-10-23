"""Lambda handler for listing open polls.

Handles GET /polls.
"""

from __future__ import annotations

from typing import Any

from shared.auth import get_caller
from shared.http import internal_error, success
from shared.logging import log_request

from .service import list_open_polls


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle GET /polls."""
    request_id = event.get("requestContext", {}).get("requestId", "unknown")
    caller = get_caller(event)

    try:
        polls = list_open_polls()
        log_request(request_id, "GET /polls", caller.user_id, "success")
        return success({"polls": polls})
    except Exception:
        log_request(request_id, "GET /polls", caller.user_id, "error")
        return internal_error()
