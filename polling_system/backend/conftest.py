"""Shared pytest fixtures for backend unit tests using moto.

Sets up mock AWS credentials and DynamoDB tables matching the
cloud architecture schema.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any

import boto3
import pytest
from moto import mock_aws

# Set mock AWS environment variables before any boto3 import
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"
os.environ["AWS_REGION"] = "ap-south-1"
os.environ["POLLS_TABLE"] = "test-polls"
os.environ["VOTES_TABLE"] = "test-votes"


@pytest.fixture
def aws_credentials() -> None:
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"


@pytest.fixture
def dynamodb_mock(aws_credentials: None) -> Generator[None]:
    """Start moto DynamoDB mock and create required tables."""
    with mock_aws():
        client = boto3.client("dynamodb", region_name="ap-south-1")

        # Create Polls table with GSI
        client.create_table(
            TableName="test-polls",
            KeySchema=[
                {"AttributeName": "pollId", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pollId", "AttributeType": "S"},
                {"AttributeName": "status", "AttributeType": "S"},
                {"AttributeName": "createdAt", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "status-createdAt-index",
                    "KeySchema": [
                        {"AttributeName": "status", "KeyType": "HASH"},
                        {"AttributeName": "createdAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )

        # Create Votes table
        client.create_table(
            TableName="test-votes",
            KeySchema=[
                {"AttributeName": "pollId", "KeyType": "HASH"},
                {"AttributeName": "userId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pollId", "AttributeType": "S"},
                {"AttributeName": "userId", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield


def make_event(
    body: dict[str, Any] | str | None = None,
    path_parameters: dict[str, str] | None = None,
    user_id: str = "test-user-sub",
    email: str = "test@example.com",
    name: str = "Test User",
) -> dict[str, Any]:
    """Build an API Gateway HTTP API proxy event with JWT authorizer claims."""
    import json

    body_str = json.dumps(body) if isinstance(body, dict) else (body or "")

    return {
        "body": body_str,
        "pathParameters": path_parameters or {},
        "requestContext": {
            "requestId": "req-123",
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": user_id,
                        "email": email,
                        "name": name,
                    }
                }
            },
        },
    }
