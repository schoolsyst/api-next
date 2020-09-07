from datetime import datetime

from pydantic import EmailStr, Field, constr
from schoolsyst_api.models import BaseModel, UserKey, userkey

UsernameStr = constr(regex=r"[\w_-]+")


class User(BaseModel):
    """
    A user account.
    """

    key: UserKey = Field(default_factory=userkey, alias="_key")
    joined_at: datetime
    username: UsernameStr  # unique
    email: EmailStr  # unique
    email_is_confirmed: bool = False


class DBUser(User):
    """
    The user, as stored in the database.
    (Note how the password is not stored in plaintext (thank god), and not even encrypted)
    """

    password_hash: str


class InUser(BaseModel):
    """
    What the user needs to provide to create an account.
    """

    username: UsernameStr
    email: EmailStr
    password: str
