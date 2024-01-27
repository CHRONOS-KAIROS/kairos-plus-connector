import json
from typing import get_args, cast, Any

import flask
from flask import current_app, request
from pydantic.error_wrappers import ValidationError

from .. import db

bp = flask.Blueprint("jobs", __name__, url_prefix="/jobs")


@bp.route("", methods=("POST",))
def create() -> dict | tuple[dict, int]:
    dbc = db.Connection(current_app.config["data_path"])
    try:
        job = db.Job.validate(request.json)
    except ValidationError as e:
        return {"message": f"Bad job specification:\n{str(e)}"}, 400
    jid = dbc.insert_job(job)
    return {"id": jid}, 201


@bp.route("/<jid>", methods=("GET",))
def get_job_by_id(jid: db.JobId) -> dict | tuple[dict, int]:
    dbc = db.Connection(current_app.config["data_path"])
    try:
        job_record = dbc.get_job_by_id(jid)
    except KeyError:
        return {"id": jid}, 404
    return job_record.dict()


@bp.route("", methods=("GET",))
def get_jobs() -> Any | tuple[Any, int]:
    dbc = db.Connection(current_app.config["data_path"])

    status = request.args.get("status", None)
    if status is not None and status not in get_args(db.Status):
        return {"message": "Invalid status."}, 400
    status = cast(db.Status | None, status)

    if status:
        records = dbc.get_jobs_by_status(status)
    else:
        records = dbc.get_jobs()
    return [r.dict() for r in records]


@bp.route("/<jid>", methods=("DELETE",))
def delete_job(jid: db.JobId) -> dict | tuple[dict, int]:
    dbc = db.Connection(current_app.config["data_path"])
    resp = {"id": jid}
    try:
        dbc.delete_job(jid)
    except KeyError:
        return resp, 404
    return resp


@bp.route("/<jid>", methods=("PATCH",))
def patch_job(jid: db.JobId) -> dict | tuple[dict, int]:
    dbc = db.Connection(current_app.config["data_path"])
    resp = {"id": jid}
    try:
        job_record = dbc.get_job_by_id(jid)
    except KeyError:
        return resp, 404
    if not isinstance(request.json, dict):
        return {"message": "Request body must by JSON mapping."}, 400
    new_data = job_record.data.dict() | request.json
    try:
        new_job = db.Job.validate(new_data)
    except ValidationError as e:
        return {"message": f"Bad job specification:\n{str(e)}"}, 400
    dbc.update_job(jid, new_job)
    return resp
