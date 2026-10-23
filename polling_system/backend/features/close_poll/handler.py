"""Lambda handler for closing a poll.

Handles POST /polls/{id}/close.
"""

from __future__ import annotations

from typing import Any

from shared.auth import get_caller
from shared.errors import ConflictError, ForbiddenError, NotFoundError
from shared.http import conflict, forbidden, internal_error, not_found, success
from shared.logging import log_request

from .service import close_poll


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle POST /polls/{id}/close."""
    request_id = event.get("requestContext", {}).get("requestId", "unknown")
    caller = get_caller(event)
    poll_id = event.get("pathParameters", {}).get("id", "")
    route = f"POST /polls/{poll_id}/close"

    try:
        result = close_poll(poll_id, caller.user_id)
        log_request(request_id, route, caller.user_id, "success")
        return success(result)
    except ForbiddenError as exc:
        log_request(request_id, route, caller.user_id, "forbidden")
        return forbidden(exc.message)
    except NotFoundError as exc:
        log_request(request_id, route, caller.user_id, "not_found")
        return not_found(exc.message)
    except ConflictError as exc:
        log_request(request_id, route, caller.user_id, "conflict")
        return conflict(exc.code, exc.message)
    except Exception:
        log_request(request_id, route, caller.user_id, "error")
        return internal_error()
