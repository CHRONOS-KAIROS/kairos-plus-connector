import shelve
from typing import TypedDict, Literal, NewType, cast, Any

import pydantic
import sdfval

Status = Literal["pending", "running", "failed", "completed"]

JobId = NewType("JobId", int)

class Job(pydantic.BaseModel):
    id: JobId
    title: str
    description: str
    status: Status
    parent: JobId | None
    sdf_data: sdfval.Document | None

    @pydantic.validator("sdf_data")
    def sdf_data_valid(cls, v: sdfval.Document | None) -> sdfval.Document | None:
        if v:
            sdfval.validate_sdf(cast(dict[str, Any], v))
        return v

    @pydantic.validator("id")
    def id_nonnegative(cls, v: JobId) -> JobId:
        assert v >= 0

# Should probably do some TDD development here since it is a good candidate.
