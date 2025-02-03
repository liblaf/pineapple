import pydantic


class DICOMDatasetMeta(pydantic.BaseModel):
    subjects: list[str] = []
