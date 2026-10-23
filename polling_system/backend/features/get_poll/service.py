"""Service layer for the get_poll feature.

Returns a single poll with the caller's vote status.
"""

from __future__ import annotations

from typing import Any

from shared.errors import NotFoundError

from .repository import get_poll_by_id, get_user_vote


def get_poll(poll_id: str, user_id: str) -> dict[str, Any]:
    """Fetch a poll and indicate whether the caller has voted.

    Raises NotFoundError if the poll does not exist.
    """
    poll = get_poll_by_id(poll_id)
    if poll is None:
        raise NotFoundError("Poll not found")

    vote = get_user_vote(poll_id, user_id)
    poll["hasVoted"] = vote is not None
    poll["userChoice"] = vote["optionId"] if vote else None

    return poll
