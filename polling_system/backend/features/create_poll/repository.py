"""Repository for the create_poll feature.

Handles all DynamoDB interactions for poll creation.
"""

from __future__ import annotations

from typing import Any

from shared.dynamo import get_table


def put_poll(poll_item: dict[str, Any]) -> None:
    """Write a new poll item to the Polls table."""
    table = get_table("POLLS_TABLE")
    table.put_item(Item=poll_item)
