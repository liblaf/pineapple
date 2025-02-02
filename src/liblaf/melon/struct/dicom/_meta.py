import pydantic

from . import Date


class DICOMMeta(pydantic.BaseModel):
    # use PascalCase for consistency with DICOM
    AcquisitionDate: Date
    PatientAge: int
    PatientBirthDate: Date
    PatientID: str
    PatientName: str
    PatientSex: str
