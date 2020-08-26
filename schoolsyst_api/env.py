from pydantic import BaseModel


class EnvironmentVariables(BaseModel):
    SECRET_KEY: str
    GITHUB_USERNAME: str
    GITHUB_TOKEN: str
    ARANGODB_USERNAME: str
    ARANGODB_HOST: str
    ARANGO_ROOT_PASSWORD: str
