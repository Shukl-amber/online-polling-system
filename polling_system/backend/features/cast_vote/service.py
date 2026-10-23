"""Service layer for the cast_vote feature.

Validates the vote request against the poll state and delegates
to the repository for the atomic transaction.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from shared.errors import ConflictError, NotFoundError, ValidationError

from .repository import get_poll_by_id, transact_cast_vote


def cast_vote(poll_id: str, option_id: str, user_id: str) -> dict[str, Any]:
    """Cast a vote for an option in a poll.

    Pre-validates that the poll exists, is open, and the option is valid
    before attempting the transaction. The transaction itself provides
    the authoritative duplicate and status checks that survive concurrency.
    """
    poll = get_poll_by_id(poll_id)
    if poll is None:
        raise NotFoundError("Poll not found")

    if poll["status"] != "open":
        raise ConflictError("POLL_CLOSED", "This poll is closed and no longer accepts votes")

    valid_option_ids = {opt["id"] for opt in poll["options"]}
    if option_id not in valid_option_ids:
        raise ValidationError("Unknown option", code="INVALID_OPTION")

    voted_at = datetime.now(UTC).isoformat()

    result = transact_cast_vote(
        poll_id=poll_id,
        user_id=user_id,
        option_id=option_id,
        voted_at=voted_at,
    )

    if result["status"] == "success":
        return {"message": "Vote recorded", "optionId": option_id}

    if result["status"] == "already_voted":
        raise ConflictError("ALREADY_VOTED", "You have already voted in this poll")

    if result["status"] == "poll_check_failed":
        # Re-read the poll to determine the exact reason
        current_poll = get_poll_by_id(poll_id)
        if current_poll is None:
            raise NotFoundError("Poll not found")
        if current_poll["status"] != "open":
            raise ConflictError("POLL_CLOSED", "This poll is closed and no longer accepts votes")
        raise NotFoundError("Poll not found")

    raise NotFoundError("Poll not found")
