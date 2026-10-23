"""Repository for the close_poll feature."""

from __future__ import annotations

from typing import Any

from boto3.dynamodb.conditions import Attr

from shared.dynamo import get_table


def get_poll_by_id(poll_id: str) -> dict[str, Any] | None:
    """Fetch a poll by primary key."""
    table = get_table("POLLS_TABLE")
    response = table.get_item(Key={"pollId": poll_id})
    return response.get("Item")


def update_poll_status(poll_id: str, new_status: str) -> None:
    """Update the status of a poll to closed."""
    table = get_table("POLLS_TABLE")
    table.update_item(
        Key={"pollId": poll_id},
        UpdateExpression="SET #st = :status",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={":status": new_status},
        ConditionExpression=Attr("pollId").exists(),
    )
