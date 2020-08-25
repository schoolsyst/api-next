"""
Defines some metadata/customization for the generated documentation systems
provided by FastAPI (namely ReDoc and SwaggerUI)
"""
import toml

import fastapi_utils.openapi
from fastapi import FastAPI

docs_urls = {"swagger": "/playground", "redoc": "/"}

pyproject = toml.load(open("pyproject.toml"))

description = (
    pyproject["tool"]["poetry"]["description"]
    + "\n\nInteractive (SwaggerUI) documentation at "
    + f"[{docs_urls['swagger']}]({docs_urls['swagger']})"
)


def edit_openapi_spec(app: FastAPI) -> None:
    fastapi_utils.openapi.simplify_operation_ids(app)
