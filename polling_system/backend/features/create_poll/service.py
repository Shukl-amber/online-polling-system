"""Service layer for the create_poll feature.

Contains business rules for creating a new poll.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from shared.auth import CallerIdentity

from .repository import put_poll
from .schema import CreatePollRequest


def create_poll(request: CreatePollRequest, caller: CallerIdentity) -> dict[str, Any]:
    """Create a new poll and return the created item.

    Generates a unique poll ID, initialises all option counts to zero,
    sets status to open, and records the creator's identity.
    """
    poll_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    options = [
        {"id": str(uuid.uuid4()), "text": text}
        for text in request.options
    ]

    counts = {opt["id"]: 0 for opt in options}

    poll_item: dict[str, Any] = {
        "pollId": poll_id,
        "title": request.title,
        "question": request.question,
        "options": options,
        "counts": counts,
        "totalVotes": 0,
        "status": "open",
        "createdBy": caller.user_id,
        "createdByName": caller.display_name,
        "createdAt": now,
    }

    put_poll(poll_item)

    return poll_item
