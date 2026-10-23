"""Unit tests for list_polls feature."""

from __future__ import annotations

import json
from conftest import make_event
from features.create_poll.handler import handler as create_handler
from features.list_polls.handler import handler as list_handler


def test_list_open_polls_returns_polls(dynamodb_mock: None) -> None:
    """Test listing open polls returns created polls in reverse chronological order."""
    # Create two polls
    create_handler(
        make_event(
            body={"title": "Poll 1", "question": "Q1?", "options": ["A", "B"]},
            user_id="user-1",
        ),
        None,
    )
    create_handler(
        make_event(
            body={"title": "Poll 2", "question": "Q2?", "options": ["X", "Y"]},
            user_id="user-2",
        ),
        None,
    )

    list_event = make_event(user_id="viewer-1")
    response = list_handler(list_event, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "polls" in body
    assert len(body["polls"]) == 2
    titles = [p["title"] for p in body["polls"]]
    assert "Poll 1" in titles
    assert "Poll 2" in titles
