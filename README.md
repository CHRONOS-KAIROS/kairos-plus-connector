# KAIROS Plus Connector

This is the CMU team's codebase for linking the schema editing and
visualization tool, OpenEra, with the LLM-based schema induction pipeline.  The
basic idea of the connector is that it provides an API to a database which
holds the shared state of the whole system.  OpenEra and the induction pipeline
can read and write state via the API in order to coordinate their operation.

## Running

The Docker image for the KAIROS Plus Connector can easily be created with:
```
nix build .#kpconn-docker
./result | docker load  # `./result` is the default output of link of nix build
docker compose up
```
The project can be built and run without nix or Docker; to do this, inspect the commands used in `flake.nix` and `docker-compose.yml`.


## File overview

- `test/` - Contains unit tests and basic integration tests.  These can be run
  with `pytest` (or `poetry run pytest`).
- `api.yml` - OpenAPI 3 spec of the API provided by the server.
- `kpconn/` - "Kairos Plus CONNector" Python package.
  - `db.py` - Database schema and operations.
  - `server/` - Flask server code.
- `pyroject.toml` - Specification for Python package; intended to be used with
  Poetry.
- `docker-compose.yml` - Description of a simple multi-container system
  including he Python server and an API visualization web app powered by
  Swagger.
- `flake.nix` - Contains recipes for building parts of the project using Nix.
