import pydantic

from liblaf import melon

from . import AcquisitionMeta, AttachmentsMeta


class PatientMeta(pydantic.BaseModel):
    acquisitions: list[AcquisitionMeta] = []
    attachments: AttachmentsMeta = []
    # use PascalCase for consistency with DICOM
    PatientAge: int
    PatientBirthDate: melon.struct.dicom.Date
    PatientID: str
    PatientName: str
    PatientSex: str
