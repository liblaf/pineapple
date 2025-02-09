import datetime
import functools

import pydicom

from liblaf.melon.typed import StrPath

type DateLike = str | datetime.datetime | datetime.date


@functools.lru_cache
def dcmread_cached(path: StrPath) -> pydicom.FileDataset:
    return pydicom.dcmread(path)


def parse_date(date: DateLike) -> datetime.date:
    match date:
        case str():
            return datetime.datetime.strptime(date, "%Y%m%d").date()  # noqa: DTZ007
        case datetime.datetime():
            return date.date()
        case datetime.date():
            return date
        case _:
            msg: str = f"Invalid date: `{date}`"
            raise ValueError(msg)


def format_date(date: datetime.date) -> str:
    return date.strftime("%Y%m%d")
