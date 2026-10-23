"""DynamoDB client helper.

Provides a shared boto3 DynamoDB resource so that every repository
uses the same client configuration and connection pooling.
"""

from __future__ import annotations

import os
from functools import lru_cache

import boto3
from mypy_boto3_dynamodb import DynamoDBServiceResource


@lru_cache(maxsize=1)
def get_dynamodb_resource() -> DynamoDBServiceResource:
    """Return a cached DynamoDB resource bound to the configured region."""
    region = os.environ.get("AWS_REGION", "ap-south-1")
    return boto3.resource("dynamodb", region_name=region)


def get_table(env_var: str):
    """Return a DynamoDB Table object from an environment variable name."""
    table_name = os.environ[env_var]
    return get_dynamodb_resource().Table(table_name)
