"""Repository for the list_polls feature.

Queries the DynamoDB Polls table using the GSI to list
open polls sorted by creation date.
"""

from __future__ import annotations

from typing import Any

from boto3.dynamodb.conditions import Key

from shared.dynamo import get_table


def query_open_polls() -> list[dict[str, Any]]:
    """Return all open polls, newest first, using the status-createdAt GSI."""
    table = get_table("POLLS_TABLE")
    response = table.query(
        IndexName="status-createdAt-index",
        KeyConditionExpression=Key("status").eq("open"),
        ScanIndexForward=False,
    )
    return response.get("Items", [])
