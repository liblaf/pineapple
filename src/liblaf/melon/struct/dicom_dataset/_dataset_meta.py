import pydantic

from . import AttachmentsMeta, PatientMeta


class DICOMDatasetMeta(pydantic.BaseModel):
    attachments: AttachmentsMeta = []
    patients: dict[str, PatientMeta] = {}
