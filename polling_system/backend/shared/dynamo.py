"""DynamoDB client helper.

Provides a shared boto3 DynamoDB resource so that every repository
uses the same client configuration and connection pooling.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import boto3


@lru_cache(maxsize=1)
def get_dynamodb_resource() -> Any:
    """Return a cached DynamoDB resource bound to the configured region."""
    region = os.environ.get("AWS_REGION", "ap-south-1")
    return boto3.resource("dynamodb", region_name=region)


def get_table(env_var: str) -> Any:
    """Return a DynamoDB Table object from an environment variable name."""
    table_name = os.environ[env_var]
    return get_dynamodb_resource().Table(table_name)
