from liblaf import melon

from . import AttachmentsMeta


class AcquisitionMeta(melon.DICOMMeta):
    attachments: AttachmentsMeta = []  # noqa: RUF012
