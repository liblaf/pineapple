from typing import Literal

import pydantic

from liblaf import melon


class SubjectMeta(pydantic.BaseModel):
    acquisitions: list[melon.struct.dicom.Date] = []
    # use PascalCase for consistency with DICOM
    PatientBirthDate: melon.struct.dicom.Date
    PatientID: str
    PatientName: str
    PatientSex: Literal["F", "M"]
