"""
Defines some metadata/customization for the generated documentation systems
provided by FastAPI (namely ReDoc and SwaggerUI)
"""
import toml

docs_urls = {"swagger": "/playground", "redoc": "/"}

pyproject = toml.load(open("pyproject.toml"))

description = (
    pyproject["tool"]["poetry"]["description"]
    + "\n\nInteractive (SwaggerUI) documentation at "
    + f"[{docs_urls['swagger']}]({docs_urls['swagger']})"
)
