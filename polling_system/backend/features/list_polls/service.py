"""Service layer for the list_polls feature.

Returns a list of open polls for display.
"""

from __future__ import annotations

from typing import Any

from .repository import query_open_polls


def list_open_polls() -> list[dict[str, Any]]:
    """Fetch all open polls, newest first.

    Returns a summary of each poll suitable for a list view,
    without the full options and counts detail.
    """
    polls = query_open_polls()
    return [
        {
            "pollId": poll["pollId"],
            "title": poll["title"],
            "question": poll["question"],
            "totalVotes": poll.get("totalVotes", 0),
            "status": poll["status"],
            "createdBy": poll["createdBy"],
            "createdByName": poll.get("createdByName", ""),
            "createdAt": poll["createdAt"],
        }
        for poll in polls
    ]
