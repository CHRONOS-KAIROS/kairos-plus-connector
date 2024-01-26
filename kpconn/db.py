import shelve
from typing import TypedDict, Literal, NewType, cast, Any, TypeVar, Callable
from pathlib import Path
import uuid

import pydantic
import sdfval

DATA_PATH = "data"

Status = Literal["pending", "running", "failed", "completed"]
JobId = NewType("JobId", str)


class Job(pydantic.BaseModel):
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


class JobRecord(pydantic.BaseModel):
    id: JobId
    data: Job


def _get_job_db() -> shelve.Shelf:
    return shelve.open(f"{DATA_PATH}/job.shelf")


def insert_job(job: Job) -> JobId:
    jid = JobId(str(uuid.uuid4()))
    with _get_job_db() as db:
        db[str(jid)] = job
    return jid


def delete_job(jid: JobId) -> None:
    with _get_job_db() as db:
        del db[jid]


def get_job_by_id(jid: JobId) -> JobRecord:
    with _get_job_db() as db:
        job = db[str(jid)]
    return JobRecord(id=jid, data=job)


def get_jobs_by_status(status: Status) -> list[JobRecord]:
    with _get_job_db() as db:
        items = [(k, v) for k, v in db.items() if v.status == status]
    return [JobRecord(id=k, data=v) for k, v in items]


def get_jobs_by_parent(parent: JobId | None) -> list[JobRecord]:
    with _get_job_db() as db:
        items = [(k, v) for k, v in db.items() if v.parent == parent]
    return [JobRecord(id=k, data=v) for k, v in items]
