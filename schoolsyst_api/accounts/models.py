from datetime import datetime

from pydantic import EmailStr, Field, constr
from schoolsyst_api.models import BaseModel, UserKey, userkey

UsernameStr = constr(regex=r"[\w_-]+")


class User(BaseModel):
    """
    Represents a user
    """

    key: UserKey = Field(default_factory=userkey, alias="_key")
    joined_at: datetime
    username: UsernameStr  # unique
    email: EmailStr  # unique
    email_is_confirmed: bool = False


class DBUser(User):
    password_hash: str


class InUser(BaseModel):
    username: UsernameStr
    email: EmailStr
    password: str
