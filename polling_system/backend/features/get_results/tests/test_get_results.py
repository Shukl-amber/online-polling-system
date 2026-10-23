"""Unit tests for get_results feature."""

from __future__ import annotations

import json
from conftest import make_event
from features.create_poll.handler import handler as create_handler
from features.cast_vote.handler import handler as vote_handler
from features.get_results.handler import handler as results_handler


def test_get_results_success(dynamodb_mock: None) -> None:
    """Test getting results returns counts, percentages, and caller choice."""
    create_res = create_handler(
        make_event(
            body={"title": "Cloud Choice", "question": "Pick one", "options": ["AWS", "GCP"]},
            user_id="creator-1",
        ),
        None,
    )
    poll_data = json.loads(create_res["body"])
    poll_id = poll_data["pollId"]
    aws_opt = poll_data["options"][0]["id"]
    gcp_opt = poll_data["options"][1]["id"]

    # Voter 1 votes AWS
    vote_handler(
        make_event(body={"optionId": aws_opt}, path_parameters={"id": poll_id}, user_id="v1"),
        None,
    )
    # Voter 2 votes AWS
    vote_handler(
        make_event(body={"optionId": aws_opt}, path_parameters={"id": poll_id}, user_id="v2"),
        None,
    )
    # Voter 3 votes GCP
    vote_handler(
        make_event(body={"optionId": gcp_opt}, path_parameters={"id": poll_id}, user_id="v3"),
        None,
    )

    # Voter 1 fetches results
    res = results_handler(
        make_event(path_parameters={"id": poll_id}, user_id="v1"),
        None,
    )

    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["totalVotes"] == 3
    assert body["userChoice"] == aws_opt

    for opt in body["options"]:
        if opt["id"] == aws_opt:
            assert opt["count"] == 2
            assert opt["percentage"] == 66.7
        elif opt["id"] == gcp_opt:
            assert opt["count"] == 1
            assert opt["percentage"] == 33.3


def test_get_results_not_found(dynamodb_mock: None) -> None:
    """Test results for nonexistent poll returns 404."""
    res = results_handler(
        make_event(path_parameters={"id": "unknown-poll"}),
        None,
    )
    assert res["statusCode"] == 404
