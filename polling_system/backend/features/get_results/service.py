"""Service layer for the get_results feature.

Computes counts, percentages, and the caller's own choice.
"""

from __future__ import annotations

from typing import Any

from shared.errors import NotFoundError

from .repository import get_poll_by_id, get_user_vote


def get_results(poll_id: str, user_id: str) -> dict[str, Any]:
    """Fetch poll results with count and percentage per option.

    Returns the total vote count, the percentage for each option
    (rounded to one decimal place), and the caller's own choice if any.
    """
    poll = get_poll_by_id(poll_id)
    if poll is None:
        raise NotFoundError("Poll not found")

    total = int(poll.get("totalVotes", 0))
    counts = poll.get("counts", {})

    options_with_results = []
    for opt in poll["options"]:
        count = int(counts.get(opt["id"], 0))
        percentage = round((count / total) * 100, 1) if total > 0 else 0.0
        options_with_results.append(
            {
                "id": opt["id"],
                "text": opt["text"],
                "count": count,
                "percentage": percentage,
            }
        )

    vote = get_user_vote(poll_id, user_id)

    return {
        "pollId": poll["pollId"],
        "title": poll["title"],
        "question": poll["question"],
        "status": poll["status"],
        "totalVotes": total,
        "options": options_with_results,
        "userChoice": vote["optionId"] if vote else None,
    }
