import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from schoolsyst_api import __version__, cors, docs, users

# It all begins here!
api = FastAPI(
    version=__version__,
    title="schoolsyst",
    description=docs.description,
    docs_url=docs.docs_urls["swagger"],
    redoc_url=docs.docs_urls["redoc"],
    default_response_class=ORJSONResponse,
)
# Handle CORS
api.add_middleware(**cors.middleware_params)
# Include routes
api.include_router(users.router, tags=["Users"])

if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)
