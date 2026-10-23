"""Authentication helpers.

Extracts the authenticated user identity from the API Gateway
JWT authorizer claims that are injected into the event by the
HTTP API's native JWT authorizer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CallerIdentity:
    """The authenticated caller extracted from JWT claims."""

    user_id: str
    display_name: str
    email: str


def get_caller(event: dict[str, Any]) -> CallerIdentity:
    """Extract the caller identity from the API Gateway event.

    The HTTP API JWT authorizer places verified claims under
    event.requestContext.authorizer.jwt.claims.
    """
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    return CallerIdentity(
        user_id=claims["sub"],
        display_name=claims.get("name", claims.get("cognito:username", "")),
        email=claims.get("email", ""),
    )
