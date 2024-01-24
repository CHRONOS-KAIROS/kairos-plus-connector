import json

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
def job_kwargs():
    return {
        "id": 0,
        "title": "sample",
        "description": "sample text",
        "status": "pending",
        "parent": 1,
        "sdf_data": valid_sdf_sample,
    }

class TestJob:
    def test_new(self, job_kwargs) -> None:
        db.Job(**job_kwargs)

    def test_new_bad_sdf(self, job_kwargs) -> None:
        with pytest.raises(ValidationError):
            job_kwargs['sdf_data'] = invalid_sdf_sample
            db.Job(**job_kwargs)

    def test_new_fail_empty(self) -> None:
        with pytest.raises(ValidationError):
            job = db.Job()  # type: ignore

    def test_new_bad_id(self, job_kwargs) -> None:
        with pytest.raises(ValidationError):
            job_kwargs["id"] = -1
            db.Job(**job_kwargs)

class TestDb:
    pass
