import datetime
from typing import Annotated

import pydantic


def parse_date(date: str | datetime.datetime | datetime.date) -> datetime.date:
    match date:
        case str():
            return datetime.datetime.strptime(date, "%Y%m%d").date()  # noqa: DTZ007
        case datetime.datetime():
            return date.date()
        case datetime.date():
            return date
        case _:
            msg: str = f"Invalid date: {date!r}"
            raise ValueError(msg)


def format_date(date: datetime.date) -> str:
    return date.strftime("%Y%m%d")


type Date = Annotated[
    datetime.date,
    pydantic.BeforeValidator(parse_date),
    pydantic.PlainSerializer(format_date, when_used="unless-none"),
]
