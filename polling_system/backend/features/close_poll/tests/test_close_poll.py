"""Unit tests for close_poll feature."""

from __future__ import annotations

import json
from conftest import make_event
from features.create_poll.handler import handler as create_handler
from features.close_poll.handler import handler as close_handler


def test_close_poll_by_creator_succeeds(dynamodb_mock: None) -> None:
    """Test poll creator can close the poll."""
    create_res = create_handler(
        make_event(
            body={"title": "Test Poll", "question": "Q?", "options": ["A", "B"]},
            user_id="creator-123",
        ),
        None,
    )
    poll_id = json.loads(create_res["body"])["pollId"]

    close_res = close_handler(
        make_event(path_parameters={"id": poll_id}, user_id="creator-123"),
        None,
    )

    assert close_res["statusCode"] == 200
    body = json.loads(close_res["body"])
    assert body["status"] == "closed"
    assert body["message"] == "Poll closed successfully"


def test_close_poll_by_non_creator_returns_403(dynamodb_mock: None) -> None:
    """Test non-creator attempting to close poll returns 403 Forbidden."""
    create_res = create_handler(
        make_event(
            body={"title": "Test Poll", "question": "Q?", "options": ["A", "B"]},
            user_id="creator-123",
        ),
        None,
    )
    poll_id = json.loads(create_res["body"])["pollId"]

    close_res = close_handler(
        make_event(path_parameters={"id": poll_id}, user_id="other-user"),
        None,
    )

    assert close_res["statusCode"] == 403
    body = json.loads(close_res["body"])
    assert "error" in body
    assert body["error"]["code"] == "FORBIDDEN"


def test_close_poll_not_found_returns_404(dynamodb_mock: None) -> None:
    """Test closing nonexistent poll returns 404."""
    close_res = close_handler(
        make_event(path_parameters={"id": "unknown-poll-id"}, user_id="user-1"),
        None,
    )
    assert close_res["statusCode"] == 404
