"""Unit tests for get_poll feature."""

from __future__ import annotations

import json
from conftest import make_event
from features.create_poll.handler import handler as create_handler
from features.get_poll.handler import handler as get_handler


def test_get_poll_success_unvoted(dynamodb_mock: None) -> None:
    """Test fetching existing poll when user has not voted."""
    create_res = create_handler(
        make_event(
            body={"title": "Cloud Providers", "question": "Q?", "options": ["AWS", "Azure"]},
            user_id="creator-1",
        ),
        None,
    )
    poll_id = json.loads(create_res["body"])["pollId"]

    get_event = make_event(
        path_parameters={"id": poll_id},
        user_id="user-99",
    )
    res = get_handler(get_event, None)

    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["pollId"] == poll_id
    assert body["hasVoted"] is False
    assert body["userChoice"] is None


def test_get_poll_not_found(dynamodb_mock: None) -> None:
    """Test fetching nonexistent poll returns 404."""
    event = make_event(path_parameters={"id": "nonexistent-id"})
    res = get_handler(event, None)

    assert res["statusCode"] == 404
    body = json.loads(res["body"])
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"
