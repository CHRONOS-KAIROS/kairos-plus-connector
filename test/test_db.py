import pytest
from kpconn import db
from pydantic.error_wrappers import ValidationError


class TestJob:
    def test_new(self, job_kwargs) -> None:
        db.Job(**job_kwargs)

    def test_new_bad_sdf(self, job_kwargs) -> None:
        sdf_data = job_kwargs["sdf_data"].copy()
        sdf_data["events"] = 19
        job_kwargs["sdf_data"] = sdf_data
        with pytest.raises(ValidationError):
            db.Job(**job_kwargs)

    def test_new_fail_empty(self) -> None:
        with pytest.raises(ValidationError):
            job = db.Job()  # type: ignore

    def test_new_extra_key(self, job_kwargs) -> None:
        with pytest.raises(ValidationError):
            db.Job(**job_kwargs, bad_key=3)


class TestDb:
    def test_insert_get_job(self, job: db.Job, dbc: db.Connection) -> None:
        jid = dbc.insert_job(job)
        assert isinstance(jid, str)
        res = dbc.get_job_by_id(jid)
        assert res.data == job
        assert res.id == jid

    @pytest.mark.skip
    def test_insert_job_invalid_sdf(self, job: db.Job, dbc: db.Connection) -> None:
        job.sdf_data["events"] = 19  # type: ignore
        with pytest.raises(ValidationError):
            jid = dbc.insert_job(job)

    def test_get_job_by_id_not_exists(self, job: db.Job, dbc: db.Connection) -> None:
        with pytest.raises(KeyError):
            dbc.get_job_by_id(db.JobId("not a key"))

    def test_get_jobs_by_status(self, job: db.Job, dbc: db.Connection) -> None:
        for _ in range(5):
            dbc.insert_job(job)
        job.status = "running"
        records = [db.JobRecord(id=dbc.insert_job(job), data=job) for _ in range(3)]
        res = dbc.get_jobs_by_status("running")
        key = lambda x: x.id
        assert sorted(res, key=key) == sorted(records, key=key)

    def test_get_jobs_by_parent(self, job: db.Job, dbc: db.Connection) -> None:
        dbc.insert_job(job)
        parent_id = dbc.insert_job(job)
        job.parent = parent_id
        records = [db.JobRecord(id=dbc.insert_job(job), data=job) for _ in range(3)]
        res = dbc.get_jobs_by_parent(parent_id)
        key = lambda x: x.id
        assert sorted(res, key=key) == sorted(records, key=key)

    def test_delete_job(self, job: db.Job, dbc: db.Connection) -> None:
        dbc.insert_job(job)
        jid = dbc.insert_job(job)
        dbc.delete_job(jid)
        with pytest.raises(KeyError):
            dbc.get_job_by_id(jid)

    def test_delete_job(self, job: db.Job, dbc: db.Connection) -> None:
        dbc.insert_job(job)
        jid = dbc.insert_job(job)
        assert job.status == "pending"
        job.status = "running"
        dbc.update_job(jid, job)
        job2 = dbc.get_job_by_id(jid).data
        assert job2.status == "running"


@pytest.mark.slow
def test_many(job: db.Job, dbc: db.Connection) -> None:
    for _ in range(10000):
        dbc.insert_job(job)
    dbc.get_jobs_by_status("pending")