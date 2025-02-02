from typing import Annotated

import pydantic

type AttachmentsMeta = Annotated[list[str], pydantic.Field(default_factory=list)]
