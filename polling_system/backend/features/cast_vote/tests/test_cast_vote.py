"""Unit tests for cast_vote feature.

Note:
True concurrency is proven on real DynamoDB in the deployed acceptance tests
(scripts/run_acceptance_tests.py, scenario T8), because in-memory mocks (moto)
do not prove multi-threaded transaction isolation or atomicity under concurrent
load. These unit tests verify the transaction parameters, sequential duplicate
prevention, closed poll rejection, and error translation.
"""

from __future__ import annotations

import json
from conftest import make_event
from features.create_poll.handler import handler as create_handler
from features.cast_vote.handler import handler as vote_handler
from features.close_poll.handler import handler as close_handler


def test_cast_vote_success(dynamodb_mock: None) -> None:
    """Test casting a valid vote on an open poll."""
    create_res = create_handler(
        make_event(
            body={"title": "Cloud Choice", "question": "Pick one", "options": ["AWS", "GCP"]},
            user_id="creator-1",
        ),
        None,
    )
    poll_data = json.loads(create_res["body"])
    poll_id = poll_data["pollId"]
    option_id = poll_data["options"][0]["id"]

    vote_event = make_event(
        body={"optionId": option_id},
        path_parameters={"id": poll_id},
        user_id="voter-1",
    )
    res = vote_handler(vote_event, None)

    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["message"] == "Vote recorded"
    assert body["optionId"] == option_id


def test_cast_vote_sequential_duplicate_returns_409(dynamodb_mock: None) -> None:
    """Test sequential duplicate vote by the same user returns 409 ALREADY_VOTED."""
    create_res = create_handler(
        make_event(
            body={"title": "Cloud Choice", "question": "Pick one", "options": ["AWS", "GCP"]},
            user_id="creator-1",
        ),
        None,
    )
    poll_data = json.loads(create_res["body"])
    poll_id = poll_data["pollId"]
    option_a = poll_data["options"][0]["id"]
    option_b = poll_data["options"][1]["id"]

    # First vote succeeds
    vote1 = vote_handler(
        make_event(
            body={"optionId": option_a},
            path_parameters={"id": poll_id},
            user_id="voter-repeat",
        ),
        None,
    )
    assert vote1["statusCode"] == 200

    # Second vote by same user (even for different option) returns 409
    vote2 = vote_handler(
        make_event(
            body={"optionId": option_b},
            path_parameters={"id": poll_id},
            user_id="voter-repeat",
        ),
        None,
    )
    assert vote2["statusCode"] == 409
    body = json.loads(vote2["body"])
    assert "error" in body
    assert body["error"]["code"] == "ALREADY_VOTED"


def test_cast_vote_on_closed_poll_returns_409(dynamodb_mock: None) -> None:
    """Test voting on a closed poll returns 409 POLL_CLOSED."""
    create_res = create_handler(
        make_event(
            body={"title": "Cloud Choice", "question": "Pick one", "options": ["AWS", "GCP"]},
            user_id="creator-1",
        ),
        None,
    )
    poll_data = json.loads(create_res["body"])
    poll_id = poll_data["pollId"]
    option_id = poll_data["options"][0]["id"]

    # Close the poll
    close_res = close_handler(
        make_event(path_parameters={"id": poll_id}, user_id="creator-1"),
        None,
    )
    assert close_res["statusCode"] == 200

    # Attempt to vote
    vote_res = vote_handler(
        make_event(
            body={"optionId": option_id},
            path_parameters={"id": poll_id},
            user_id="voter-late",
        ),
        None,
    )
    assert vote_res["statusCode"] == 409
    body = json.loads(vote_res["body"])
    assert body["error"]["code"] == "POLL_CLOSED"


def test_cast_vote_unknown_poll_returns_404(dynamodb_mock: None) -> None:
    """Test voting on nonexistent poll returns 404."""
    vote_res = vote_handler(
        make_event(
            body={"optionId": "opt-123"},
            path_parameters={"id": "nonexistent-poll"},
            user_id="voter-1",
        ),
        None,
    )
    assert vote_res["statusCode"] == 404


def test_cast_vote_invalid_option_returns_400(dynamodb_mock: None) -> None:
    """Test voting for nonexistent option returns 400 INVALID_OPTION."""
    create_res = create_handler(
        make_event(
            body={"title": "Cloud Choice", "question": "Pick one", "options": ["AWS", "GCP"]},
            user_id="creator-1",
        ),
        None,
    )
    poll_id = json.loads(create_res["body"])["pollId"]

    vote_res = vote_handler(
        make_event(
            body={"optionId": "invalid-opt-id"},
            path_parameters={"id": poll_id},
            user_id="voter-1",
        ),
        None,
    )
    assert vote_res["statusCode"] == 400
    body = json.loads(vote_res["body"])
    assert body["error"]["code"] == "INVALID_OPTION"
