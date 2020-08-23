from pathlib import Path

import typed_dotenv
import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from schoolsyst_api import (
    __version__,
    accounts,
    cors,
    database,
    docs,
    events,
    homework,
    settings,
    subjects,
)
from schoolsyst_api.env import EnvironmentVariables

# It all begins here!
api = FastAPI(
    version=__version__,
    title="schoolsyst",
    description=docs.description,
    docs_url=docs.docs_urls["swagger"],
    redoc_url=docs.docs_urls["redoc"],
    default_response_class=ORJSONResponse,
)
# Load environment variables (to validate)
typed_dotenv.load_into(EnvironmentVariables, Path(__file__).parent.parent / ".env")
# Initialize the database
api.add_event_handler("startup", database.initialize)
# Handle CORS
api.add_middleware(**cors.middleware_params)
# Include routes
api.include_router(accounts.router, tags=["Accounts"])
api.include_router(subjects.router, tags=["Subjects"])
api.include_router(homework.router, tags=["Homework"])
api.include_router(settings.router, tags=["Settings"])
api.include_router(events.router, tags=["Schedule"])

if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)
