"""Service layer for the close_poll feature.

Only the poll creator can close a poll.
"""

from __future__ import annotations

from typing import Any

from shared.errors import ConflictError, ForbiddenError, NotFoundError

from .repository import get_poll_by_id, update_poll_status


def close_poll(poll_id: str, user_id: str) -> dict[str, Any]:
    """Close a poll so it no longer accepts votes.

    Only the original creator is allowed to close the poll.
    Returns the updated poll summary.
    """
    poll = get_poll_by_id(poll_id)
    if poll is None:
        raise NotFoundError("Poll not found")

    if poll["createdBy"] != user_id:
        raise ForbiddenError("Only the poll creator can close this poll")

    if poll["status"] == "closed":
        raise ConflictError("POLL_CLOSED", "This poll is already closed")

    update_poll_status(poll_id, "closed")

    return {
        "pollId": poll_id,
        "status": "closed",
        "message": "Poll closed successfully",
    }
