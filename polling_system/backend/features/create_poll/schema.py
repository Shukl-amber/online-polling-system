"""Validation schemas for the create_poll feature."""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class CreatePollRequest(BaseModel):
    """Schema for creating a new poll."""

    title: str
    question: str
    options: list[str]

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Title must be 3 to 120 characters after trimming."""
        v = v.strip()
        if len(v) < 3:
            msg = "Title must be at least 3 characters"
            raise ValueError(msg)
        if len(v) > 120:
            msg = "Title must be at most 120 characters"
            raise ValueError(msg)
        return v

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Question must be at most 300 characters after trimming."""
        v = v.strip()
        if not v:
            msg = "Question is required"
            raise ValueError(msg)
        if len(v) > 300:
            msg = "Question must be at most 300 characters"
            raise ValueError(msg)
        return v

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[str]) -> list[str]:
        """Between 2 and 6 unique options, each 1 to 80 characters."""
        trimmed = [opt.strip() for opt in v]

        for opt in trimmed:
            if len(opt) < 1:
                msg = "Each option must be at least 1 character"
                raise ValueError(msg)
            if len(opt) > 80:
                msg = "Each option must be at most 80 characters"
                raise ValueError(msg)

        if len(trimmed) < 2:
            msg = "A poll must have at least 2 options"
            raise ValueError(msg)
        if len(trimmed) > 6:
            msg = "A poll must have at most 6 options"
            raise ValueError(msg)

        # Check uniqueness after trimming and ignoring case
        lower_set: set[str] = set()
        for opt in trimmed:
            key = opt.lower()
            if key in lower_set:
                msg = f"Duplicate option: {opt}"
                raise ValueError(msg)
            lower_set.add(key)

        return trimmed
