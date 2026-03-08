from __future__ import annotations

import datetime
from typing import Any

import pydantic


class EntryMetadataModel(pydantic.BaseModel):
    key: str
    ctime: datetime.datetime
    user: dict[str, Any] = pydantic.Field(default_factory=dict)

    @pydantic.field_validator("ctime")
    @classmethod
    def _validate_ctime_timezone(cls, value: datetime.datetime) -> datetime.datetime:
        if value.tzinfo is None:
            raise ValueError
        return value

    @classmethod
    def new(cls, *, key: str, user: dict[str, Any] | None = None) -> EntryMetadataModel:
        return cls(
            key=key, ctime=datetime.datetime.now(tz=datetime.UTC), user=user or {}
        )


__all__ = ["EntryMetadataModel"]
