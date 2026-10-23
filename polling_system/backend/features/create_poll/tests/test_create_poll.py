"""Unit tests for create_poll feature."""

from __future__ import annotations

import json
from conftest import make_event
from features.create_poll.handler import handler


def test_create_poll_success(dynamodb_mock: None) -> None:
    """Test successful poll creation with valid inputs."""
    event = make_event(
        body={
            "title": "Cloud Providers",
            "question": "Which cloud provider do you prefer?",
            "options": ["AWS", "Azure", "GCP"],
        },
        user_id="user-123",
        name="Amber Shukla",
    )

    response = handler(event, None)
    assert response["statusCode"] == 201

    body = json.loads(response["body"])
    assert body["title"] == "Cloud Providers"
    assert body["question"] == "Which cloud provider do you prefer?"
    assert len(body["options"]) == 3
    assert body["status"] == "open"
    assert body["totalVotes"] == 0
    assert body["createdBy"] == "user-123"
    assert body["createdByName"] == "Amber Shukla"

    # All option counts initialised to 0
    for opt in body["options"]:
        assert body["counts"][opt["id"]] == 0


def test_create_poll_validation_too_few_options(dynamodb_mock: None) -> None:
    """Test validation failure with fewer than 2 options."""
    event = make_event(
        body={
            "title": "Cloud Providers",
            "question": "Question?",
            "options": ["Only One"],
        }
    )

    response = handler(event, None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_create_poll_validation_duplicate_options(dynamodb_mock: None) -> None:
    """Test validation failure with duplicate options (case-insensitive)."""
    event = make_event(
        body={
            "title": "Cloud Providers",
            "question": "Question?",
            "options": ["AWS", "aws", "GCP"],
        }
    )

    response = handler(event, None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_create_poll_validation_title_too_short(dynamodb_mock: None) -> None:
    """Test validation failure when title is under 3 characters."""
    event = make_event(
        body={
            "title": "Hi",
            "question": "Question?",
            "options": ["Option A", "Option B"],
        }
    )

    response = handler(event, None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"]["code"] == "VALIDATION_ERROR"
