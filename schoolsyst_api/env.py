from pydantic import AnyHttpUrl, BaseModel


class EnvironmentVariables(BaseModel):
    SECRET_KEY: str
    GITHUB_USERNAME: str
    GITHUB_TOKEN: str
    ARANGODB_USERNAME: str
    ARANGODB_HOST: AnyHttpUrl
    ARANGO_ROOT_PASSWORD: str
    GMAIL_USERNAME: str
    GMAIL_PASSWORD: str
