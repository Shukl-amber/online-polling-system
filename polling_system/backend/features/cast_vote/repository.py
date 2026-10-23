"""Repository for the cast_vote feature.

Executes the atomic DynamoDB transaction that records a vote
and increments the poll counts in a single all-or-nothing operation.
"""

from __future__ import annotations

import os
from typing import Any

import boto3

from shared.dynamo import get_table


def get_poll_by_id(poll_id: str) -> dict[str, Any] | None:
    """Fetch a poll by primary key for pre-transaction validation."""
    table = get_table("POLLS_TABLE")
    response = table.get_item(Key={"pollId": poll_id})
    return response.get("Item")


def transact_cast_vote(
    poll_id: str,
    user_id: str,
    option_id: str,
    voted_at: str,
) -> dict[str, str]:
    """Execute the atomic vote transaction.

    Two actions in one transaction:
    1. Put into Votes with condition that no item with (pollId, userId) exists.
       This is the mechanism that blocks duplicate votes.
    2. Update the poll: increment counts[optionId] and totalVotes,
       with conditions that the poll exists and status is open.

    Returns a dict with the outcome: {"status": "success"} or raises.
    """
    polls_table = os.environ["POLLS_TABLE"]
    votes_table = os.environ["VOTES_TABLE"]
    region = os.environ.get("AWS_REGION", "ap-south-1")

    client = boto3.client("dynamodb", region_name=region)

    try:
        client.transact_write_items(
            TransactItems=[
                {
                    "Put": {
                        "TableName": votes_table,
                        "Item": {
                            "pollId": {"S": poll_id},
                            "userId": {"S": user_id},
                            "optionId": {"S": option_id},
                            "votedAt": {"S": voted_at},
                        },
                        "ConditionExpression": "attribute_not_exists(pollId) AND attribute_not_exists(userId)",
                    }
                },
                {
                    "Update": {
                        "TableName": polls_table,
                        "Key": {
                            "pollId": {"S": poll_id},
                        },
                        "UpdateExpression": (
                            "SET counts.#optId = counts.#optId + :one, "
                            "totalVotes = totalVotes + :one"
                        ),
                        "ExpressionAttributeNames": {
                            "#optId": option_id,
                            "#st": "status",
                        },
                        "ExpressionAttributeValues": {
                            ":one": {"N": "1"},
                            ":open": {"S": "open"},
                        },
                        "ConditionExpression": (
                            "attribute_exists(pollId) AND #st = :open"
                        ),
                    }
                },
            ]
        )
        # Need to also add #st to the Update's ExpressionAttributeNames
    except client.exceptions.TransactionCanceledException as exc:
        reasons = exc.response.get("CancellationReasons", [])
        return _interpret_cancellation(reasons)

    return {"status": "success"}


def _interpret_cancellation(reasons: list[dict[str, Any]]) -> dict[str, str]:
    """Interpret the cancellation reasons from a failed transaction.

    Index 0 = the Put into Votes (duplicate check)
    Index 1 = the Update on Polls (exists and open check)
    """
    vote_reason = reasons[0].get("Code", "None") if len(reasons) > 0 else "None"
    poll_reason = reasons[1].get("Code", "None") if len(reasons) > 1 else "None"

    if vote_reason == "ConditionalCheckFailed":
        return {"status": "already_voted"}

    if poll_reason == "ConditionalCheckFailed":
        return {"status": "poll_check_failed"}

    return {"status": "unknown_failure"}
