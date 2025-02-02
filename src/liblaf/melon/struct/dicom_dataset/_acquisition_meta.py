import pydantic

from liblaf import melon


class AcquisitionMeta(melon.DICOMMeta):
    attachments: list[str] = pydantic.Field(default_factory=list)
