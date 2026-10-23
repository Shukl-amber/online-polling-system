"""Repository for the get_results feature."""

from __future__ import annotations

from typing import Any

from shared.dynamo import get_table


def get_poll_by_id(poll_id: str) -> dict[str, Any] | None:
    """Fetch a poll by primary key."""
    table = get_table("POLLS_TABLE")
    response = table.get_item(Key={"pollId": poll_id})
    return response.get("Item")


def get_user_vote(poll_id: str, user_id: str) -> dict[str, Any] | None:
    """Fetch a user's vote for a poll."""
    table = get_table("VOTES_TABLE")
    response = table.get_item(Key={"pollId": poll_id, "userId": user_id})
    return response.get("Item")
