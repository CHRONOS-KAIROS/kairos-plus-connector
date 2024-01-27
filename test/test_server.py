import uuid

import pytest

from kpconn.server.app import create_app
from kpconn import db


@pytest.fixture
def jid(client, job) -> db.JobId:
    resp = client.post("/jobs", json=job.dict())
    return resp.json["id"]


class TestSever:
    def test_hello(self, client) -> None:
        resp = client.get("/hello")
        data = resp.json

        assert data["message"] == "Hello, World!"

    def test_create_job(self, client, job) -> None:
        resp = client.post("/jobs", json=job.dict())
        assert resp.status_code == 201
        uuid.UUID(resp.json["id"])

    def test_create_job_invalid_sdf(self, client, job) -> None:
        job.sdf_data["events"] = 19
        resp = client.post("/jobs", json=job.dict())
        assert resp.status_code == 400

    def test_create_job_invalid_job(self, client, job) -> None:
        resp = client.post("/jobs", json={"foo": "bar"})
        assert resp.status_code == 400

    def test_create_job_invalid_json_request(self, client, job) -> None:
        resp = client.post("/jobs", data="{bad")
        assert resp.status_code == 415

    def test_get_job(self, client, job, jid) -> None:
        resp = client.get(f"/jobs/{jid}")
        assert resp.status_code == 200
        assert resp.json["id"] == jid
        assert resp.json["data"] == job.dict()

    def test_get_job_not_found(self, client, job) -> None:
        resp = client.get(f"/jobs/not-here")
        assert resp.status_code == 404

    def test_delete_job(self, client, jid) -> None:
        resp = client.delete(f"/jobs/{jid}")
        assert resp.status_code == 200
        resp = client.get(f"/jobs/{jid}")
        assert resp.status_code == 404

    def test_delete_job_not_found(self, client, job) -> None:
        resp = client.delete(f"/jobs/not-there")
        assert resp.status_code == 404

    def test_patch_job(self, client, jid) -> None:
        resp = client.get(f"/jobs/{jid}")
        assert "pending" == resp.json["data"]["status"]
        resp = client.patch(f"/jobs/{jid}", json={"status": "running"})
        assert resp.status_code == 200
        resp = client.get(f"/jobs/{jid}")
        assert "running" == resp.json["data"]["status"]

    def test_patch_job_not_dict(self, client, jid) -> None:
        resp = client.patch(f"/jobs/{jid}", json="not a dict")
        assert resp.status_code == 400

    def test_patch_job_bad_spec(self, client, jid) -> None:
        resp = client.patch(f"/jobs/{jid}", json={"status": "not a status"})
        assert resp.status_code == 400
        resp = client.patch(f"/jobs/{jid}", json={"bad key": 3})
        assert resp.status_code == 400

    def test_pending(self, client, job) -> None:
        jid_resps = [client.post("/jobs", json=job.dict()) for _ in range(3)]
        job2 = job.copy()
        job2.status = "running"
        for _ in range(3):
            client.post("/jobs", json=job2.dict())
        resp = client.get("/jobs", query_string={"status": "pending"})
        assert resp.status_code == 200
        res_records = resp.json
        orig_records = [
            {"id": resp.json["id"], "data": job.dict()} for resp in jid_resps
        ]
        key = lambda x: x["id"]
        orig_sorted = sorted(orig_records, key=key)
        results_sorted = sorted(res_records, key=key)
        assert all([rec["data"]["status"] == "pending" for rec in res_records])
        assert orig_sorted == results_sorted

    def test_pending_bad_status(self, client) -> None:
        resp = client.get("/jobs", query_string={"status": "not_a_status"})
        assert resp.status_code == 400
