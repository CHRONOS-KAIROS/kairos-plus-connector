import functools
from typing import Iterator, Any
import json

import flask
import flask.testing
import pytest
import sdfval

from kpconn import db
from kpconn.server.app import create_app


@pytest.fixture
def app(tmp_path) -> Iterator[flask.Flask]:
    app = create_app({"data_path": tmp_path})
    yield app


@pytest.fixture
def client(app: flask.Flask) -> flask.testing.FlaskClient:
    return app.test_client()


@functools.cache
def get_valid_sdf() -> sdfval.Document:
    with open("test/data/consume.json") as fo:
        sdf_data = json.load(fo)
    return sdfval.validate_sdf(sdf_data)


# invalid_sdf_sample = valid_sdf_sample.copy()
# invalid_sdf_sample["events"] = 19  # type: ignore


@pytest.fixture
def job_kwargs() -> Any:
    return {
        "title": "sample",
        "description": "sample text",
        "status": "pending",
        "parent": None,
        "sdf_data": get_valid_sdf(),
    }


@pytest.fixture
def job(job_kwargs) -> db.Job:
    return db.Job(**job_kwargs)


@pytest.fixture
def dbc(tmp_path) -> Iterator[db.Connection]:
    dbc = db.Connection(tmp_path)
    yield dbc
    dbc.close()
