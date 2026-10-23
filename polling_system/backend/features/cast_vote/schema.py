"""Validation schemas for the cast_vote feature."""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class CastVoteRequest(BaseModel):
    """Schema for casting a vote."""

    optionId: str

    @field_validator("optionId")
    @classmethod
    def validate_option_id(cls, v: str) -> str:
        """Option ID must be a non-empty string."""
        v = v.strip()
        if not v:
            msg = "optionId is required"
            raise ValueError(msg)
        return v
