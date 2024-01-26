import json
import shelve
from typing import Iterator, Any
import uuid

import pytest
from kpconn import db
import sdfval
from pydantic.error_wrappers import ValidationError

with open("test/data/consume.json") as fo:
    sdf_data = json.load(fo)
valid_sdf_sample = sdfval.validate_sdf(sdf_data)

invalid_sdf_sample = valid_sdf_sample.copy()
invalid_sdf_sample["events"] = 19  # type: ignore


@pytest.fixture
def job_kwargs() -> Any:
    return {
        "title": "sample",
        "description": "sample text",
        "status": "pending",
        "parent": None,
        "sdf_data": valid_sdf_sample,
    }


@pytest.fixture
def job(job_kwargs) -> db.Job:
    return db.Job(**job_kwargs)


class TestJob:
    def test_new(self, job_kwargs) -> None:
        db.Job(**job_kwargs)

    def test_new_bad_sdf(self, job_kwargs) -> None:
        with pytest.raises(ValidationError):
            job_kwargs["sdf_data"] = invalid_sdf_sample
            db.Job(**job_kwargs)

    def test_new_fail_empty(self) -> None:
        with pytest.raises(ValidationError):
            job = db.Job()  # type: ignore


@pytest.fixture
def job_db(tmp_path) -> Iterator[None]:
    DATA_PATH = db.DATA_PATH
    db.DATA_PATH = tmp_path
    yield None
    db.DATA_PATH = DATA_PATH


class TestDb:
    def test_insert_get_job(self, job: db.Job, job_db) -> None:
        jid = db.insert_job(job)
        assert isinstance(jid, str)
        res = db.get_job_by_id(jid)
        assert res.data == job
        assert res.id == jid

    def test_get_job_by_id_not_exists(self, job: db.Job, job_db) -> None:
        with pytest.raises(KeyError):
            db.get_job_by_id(db.JobId("not a key"))

    def test_get_jobs_by_status(self, job: db.Job, job_db) -> None:
        for _ in range(5):
            db.insert_job(job)
        job.status = "running"
        records = [db.JobRecord(id=db.insert_job(job), data=job) for _ in range(3)]
        res = db.get_jobs_by_status("running")
        key = lambda x: x.id
        assert sorted(res, key=key) == sorted(records, key=key)

    def test_get_jobs_by_parent(self, job: db.Job, job_db) -> None:
        db.insert_job(job)
        parent_id = db.insert_job(job)
        job.parent = parent_id
        records = [db.JobRecord(id=db.insert_job(job), data=job) for _ in range(3)]
        res = db.get_jobs_by_parent(parent_id)
        key = lambda x: x.id
        assert sorted(res, key=key) == sorted(records, key=key)

    def test_delete_job(self, job: db.Job, job_db) -> None:
        db.insert_job(job)
        jid = db.insert_job(job)
        db.delete_job(jid)
        with pytest.raises(KeyError):
            db.get_job_by_id(jid)


@pytest.mark.slow
def test_many(job: db.Job, job_db) -> None:
    for _ in range(10000):
        db.insert_job(job)
    db.get_jobs_by_status("pending")
