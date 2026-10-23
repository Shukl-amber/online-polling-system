"""Lambda handler for fetching a single poll.

Handles GET /polls/{id}.
"""

from __future__ import annotations

from typing import Any

from shared.auth import get_caller
from shared.errors import NotFoundError
from shared.http import internal_error, not_found, success
from shared.logging import log_request

from .service import get_poll


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle GET /polls/{id}."""
    request_id = event.get("requestContext", {}).get("requestId", "unknown")
    caller = get_caller(event)
    poll_id = event.get("pathParameters", {}).get("id", "")

    try:
        poll = get_poll(poll_id, caller.user_id)
        log_request(request_id, f"GET /polls/{poll_id}", caller.user_id, "success")
        return success(poll)
    except NotFoundError as exc:
        log_request(request_id, f"GET /polls/{poll_id}", caller.user_id, "not_found")
        return not_found(exc.message)
    except Exception:
        log_request(request_id, f"GET /polls/{poll_id}", caller.user_id, "error")
        return internal_error()
