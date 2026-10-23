"""Lambda handler for casting a vote.

Handles POST /polls/{id}/vote.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from shared.auth import get_caller
from shared.errors import ConflictError, NotFoundError, ValidationError
from shared.http import bad_request, conflict, internal_error, not_found, success
from shared.logging import log_request

from .schema import CastVoteRequest
from .service import cast_vote


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle POST /polls/{id}/vote."""
    request_id = event.get("requestContext", {}).get("requestId", "unknown")
    caller = get_caller(event)
    poll_id = event.get("pathParameters", {}).get("id", "")
    route = f"POST /polls/{poll_id}/vote"

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        log_request(request_id, route, caller.user_id, "invalid_json")
        return bad_request("INVALID_JSON", "Request body must be valid JSON")

    try:
        request = CastVoteRequest(**body)
    except PydanticValidationError as exc:
        first_error = exc.errors()[0]
        message = first_error.get("msg", "Validation error")
        log_request(request_id, route, caller.user_id, "validation_error")
        return bad_request("VALIDATION_ERROR", message)

    try:
        result = cast_vote(poll_id, request.optionId, caller.user_id)
        log_request(request_id, route, caller.user_id, "success")
        return success(result)
    except ValidationError as exc:
        log_request(request_id, route, caller.user_id, "validation_error")
        return bad_request(exc.code, exc.message)
    except NotFoundError as exc:
        log_request(request_id, route, caller.user_id, "not_found")
        return not_found(exc.message)
    except ConflictError as exc:
        log_request(request_id, route, caller.user_id, "conflict", {"code": exc.code})
        return conflict(exc.code, exc.message)
    except Exception:
        log_request(request_id, route, caller.user_id, "error")
        return internal_error()
