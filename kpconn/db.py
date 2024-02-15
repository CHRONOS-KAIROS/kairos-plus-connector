import shelve
from typing import TypedDict, Literal, NewType, cast, Any, TypeVar, Callable
from pathlib import Path
import uuid
import datetime


import pydantic
import sdfval

Status = Literal["pending", "running", "failed", "completed"]
JobId = NewType("JobId", str)


class Job(pydantic.BaseModel):
    title: str
    raw_title: str | None
    error_message: str | None
    last_updated: datetime.datetime | None
    description: str
    status: Status
    parent: JobId | None
    generated_for: sdfval.sdf.DocumentId | None
    sdf_data: sdfval.Document | None

    class Config:
        extra = "forbid"

    @pydantic.validator("sdf_data")
    def sdf_data_valid(cls, v: sdfval.Document | None) -> sdfval.Document | None:
        if v:
            sdfval.validate_sdf(cast(dict[str, Any], v))
        return v


class JobRecord(pydantic.BaseModel):
    id: JobId
    data: Job


def update_job_timestamp(job: Job) -> None:
    job.last_updated = datetime.datetime.now().isoformat() + "Z"


class Connection:
    def __init__(self, data_path: str) -> None:
        Path(data_path).mkdir(exist_ok=True, parents=True)
        self.db = shelve.open(f"{data_path}/job.shelf")
        self.data_path = data_path

    def insert_job(self, job: Job) -> JobId:
        jid = JobId(str(uuid.uuid4()))
        update_job_timestamp(job)
        self.db[str(jid)] = job
        return jid

    def delete_job(self, jid: JobId) -> None:
        del self.db[jid]

    def get_job_by_id(self, jid: JobId) -> JobRecord:
        job = self.db[str(jid)]
        return JobRecord(id=jid, data=job)

    def update_job(self, jid: JobId, job: Job) -> JobRecord:
        self.db[jid] = job
        update_job_timestamp(job)
        return JobRecord(id=jid, data=job)

    def get_jobs(self) -> list[JobRecord]:
        items = [(k, v) for k, v in self.db.items()]
        return [JobRecord(id=k, data=v) for k, v in items]

    def get_jobs_by_status(self, status: Status) -> list[JobRecord]:
        items = [(k, v) for k, v in self.db.items() if v.status == status]
        return [JobRecord(id=k, data=v) for k, v in items]

    def get_jobs_by_parent(self, parent: JobId | None) -> list[JobRecord]:
        items = [(k, v) for k, v in self.db.items() if v.parent == parent]
        return [JobRecord(id=k, data=v) for k, v in items]

    def close(self) -> None:
        self.db.close()

    def __del__(self) -> None:
        self.close()
