import datetime
from typing import Annotated, Literal

import pydantic

from . import format_date, parse_date

type Date = Annotated[
    datetime.date,
    pydantic.BeforeValidator(parse_date),
    pydantic.PlainSerializer(format_date, when_used="unless-none"),
]


class DICOMMeta(pydantic.BaseModel):
    # use PascalCase for consistency with DICOM
    AcquisitionDate: Date
    PatientAge: int
    PatientBirthDate: Date
    PatientID: str
    PatientName: str
    PatientSex: Literal["F", "M"]
