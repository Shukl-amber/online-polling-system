"""Structured JSON logging for Lambda functions.

Emits one JSON line per log call so that CloudWatch Logs Insights
can query by request_id, route, user_id or outcome.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("polling_system")
logger.setLevel(logging.INFO)


def log_request(
    request_id: str,
    route: str,
    user_id: str,
    outcome: str,
    detail: dict[str, Any] | None = None,
) -> None:
    """Emit one structured log line for a request."""
    entry: dict[str, Any] = {
        "request_id": request_id,
        "route": route,
        "user_id": user_id,
        "outcome": outcome,
    }
    if detail:
        entry["detail"] = detail
    logger.info(json.dumps(entry, default=str))
