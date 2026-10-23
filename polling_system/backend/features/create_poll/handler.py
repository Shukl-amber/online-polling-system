"""Lambda handler for creating a poll.

Parses the request, delegates to the service layer,
and returns a structured response. Never contains business logic.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from shared.auth import get_caller
from shared.http import bad_request, created, internal_error
from shared.logging import log_request

from .service import create_poll


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle POST /polls."""
    request_id = event.get("requestContext", {}).get("requestId", "unknown")
    caller = get_caller(event)

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        log_request(request_id, "POST /polls", caller.user_id, "invalid_json")
        return bad_request("INVALID_JSON", "Request body must be valid JSON")

    try:
        from .schema import CreatePollRequest

        request = CreatePollRequest(**body)
    except ValidationError as exc:
        first_error = exc.errors()[0]
        message = first_error.get("msg", "Validation error")
        log_request(
            request_id, "POST /polls", caller.user_id, "validation_error",
            {"message": message},
        )
        return bad_request("VALIDATION_ERROR", message)

    try:
        poll = create_poll(request, caller)
        log_request(
            request_id, "POST /polls", caller.user_id, "created",
            {"poll_id": poll["pollId"]},
        )
        return created(poll)
    except Exception:
        log_request(request_id, "POST /polls", caller.user_id, "error")
        return internal_error()
