from pathlib import Path

import schoolsyst_api.grades.routes
import schoolsyst_api.homework.routes
import schoolsyst_api.schedule.routes
import schoolsyst_api.settings.routes
import schoolsyst_api.statistics.routes
import schoolsyst_api.subjects.routes
import typed_dotenv
import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from schoolsyst_api import __version__, accounts, cors, database, docs
from schoolsyst_api.docs import edit_openapi_spec
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
api.include_router(schoolsyst_api.subjects.routes.router, tags=["Subjects"])
api.include_router(schoolsyst_api.homework.routes.router, tags=["Homework"])
api.include_router(schoolsyst_api.settings.routes.router, tags=["Settings"])
api.include_router(schoolsyst_api.schedule.routes.router, tags=["Schedule"])
api.include_router(schoolsyst_api.grades.routes.router, tags=["Grades"])
api.include_router(schoolsyst_api.statistics.routes.router, tags=["Statistics"])
# Modify the OpenAPI spec
edit_openapi_spec(api)

if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)
