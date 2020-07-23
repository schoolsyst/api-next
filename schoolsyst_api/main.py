import uvicorn
from fastapi import FastAPI
from schoolsyst_api import auth, cors
from schoolsyst_api import __version__
import toml

# Extract some vars from pyproject.toml to use with FastAPI()
pyproject = toml.load(open("pyproject.toml"))
api = FastAPI(
    version=__version__,
    title="schoolsyst",
    description=pyproject["tool"]["poetry"]["description"],
)
api.add_middleware(**cors.middleware_params)
api.include_router(auth.router, tags=["Users"])

if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)
