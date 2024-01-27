from typing import Any
from flask_cors import CORS  # type: ignore


import flask


def create_app(config: dict[str, Any] | None = None) -> flask.Flask:
    app = flask.Flask(__name__, instance_relative_config=True)

    app.config.update(
        data_path="data",
    )

    if config is not None:
        app.config.update(**config)

    from . import job

    app.register_blueprint(job.bp)

    @app.route("/hello")
    def hello_world() -> dict:
        return {"message": "Hello, World!"}

    CORS(app)
    return app
