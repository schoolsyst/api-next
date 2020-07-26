import toml

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from schoolsyst_api import __version__, auth, cors

# Extract some vars from pyproject.toml to use with FastAPI()
SWAGGER_UI_DOCS_URL="/playground"
pyproject = toml.load(open("pyproject.toml"))
api = FastAPI(
    version=__version__,
    title="schoolsyst",
    description=pyproject["tool"]["poetry"]["description"]
    + f"\n\nInteractive (SwaggerUI) documentation at [{SWAGGER_UI_DOCS_URL}]({SWAGGER_UI_DOCS_URL})",
    default_response_class=ORJSONResponse,
    docs_url=SWAGGER_UI_DOCS_URL,
    redoc_url="/",
)
api.add_middleware(**cors.middleware_params)
api.include_router(auth.router, tags=["Users"])

if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)
