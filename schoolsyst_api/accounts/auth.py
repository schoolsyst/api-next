import os
from datetime import timedelta
from typing import *

from arango.database import StandardDatabase
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from parse import parse
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from schoolsyst_api import database
from schoolsyst_api.accounts import create_jwt_token, get_user, router
from schoolsyst_api.accounts.models import DBUser, UsernameStr
from schoolsyst_api.utils import make_json_serializable
from zxcvbn import zxcvbn

load_dotenv(".env")
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_SIGN_ALGORITHM = "HS256"

ACCESS_TOKEN_VALID_FOR = timedelta(minutes=3)
JWT_SUB_FORMAT = "username:{}"


class Token(BaseModel):
    """As defined by OAuth 2"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Models the data in the JWT token's payload"""

    username: str


# Context for password hashing
password_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Special FastAPI class to inject as a dependency
# and get appropriate openapi.json integration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


def is_password_strong_enough(password_analysis: Dict[str, Any]) -> bool:
    return password_analysis["score"] >= 2


def analyze_password(
    password: str, username: str, email: str
) -> Optional[Dict[str, Any]]:
    return zxcvbn(password, [email, username])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that the plain_password matches against a hash `hashed_password`

    >>> verify_password(
    ...     "correct-battery-horse-staple",
    ...     "$argon2id$v=19$m=102400,t=2,p=8$h/Bea41xjlEqBQAgpPTemw$tprEaXUjIeEP+B9ryxSVAw"
    ... )
    True
    >>> verify_password(
    ...     "correct-battery-horse-staple",
    ...     "$argon2id$v=19$m=102400,t=2,p=8$h/Bea41xjlEqBQAgpkTemw$tprEaXUjIeEP+B9ryxSVAw"
    ... )
    False
    >>> verify_password("correct-battery-horse-staple", "hunter2")
    False
    """
    try:
        return password_context.verify(plain_password, hashed_password)
    except ValueError:
        return False


def hash_password(plain_password: str) -> str:
    """
    Hash the plain password

    >>> hash_password("porte-derobee-fire-water-plants").startswith('$argon2')
    True
    """
    return password_context.hash(plain_password)


def extract_username_from_jwt_payload(payload: dict) -> Optional[str]:
    """
    Extract the username from the JWT's `sub`.
    The sub is of the form <resource type>:<resource>
    Here we expect a username, so <resource type> needs to be `username`.
    If <resource type> is not `username`, if the `sub` does not have the correct form
    or if `sub` is not in the `payload`, return `None`.

    >>> extract_username_from_jwt_payload({"sub": "bertrand"})
    >>> extract_username_from_jwt_payload({"sub": "username:ambre"})
    'ambre'
    >>> extract_username_from_jwt_payload({"sub": "usaanam:ambre"})
    >>> extract_username_from_jwt_payload({})
    """
    if (subject := payload.get("sub")) is None:
        return None
    if (username := parse(JWT_SUB_FORMAT, subject)) is None:
        return None
    return username[0]


def authenticate_user(
    db: StandardDatabase, username: str, password: str
) -> Union[DBUser, Literal[False]]:
    """
    Tries to authentificate the user with `username` and `password`.
    Returns `False` if the password is incorrect or if the user is not found.
    """
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


@router.post("/auth/")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: StandardDatabase = Depends(database.get),
) -> Token:
    # Try to auth the user
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Create the access token
    access_token = create_jwt_token(
        sub_format=JWT_SUB_FORMAT,
        sub_value=user.username,
        valid_for=ACCESS_TOKEN_VALID_FOR,
    )
    # Return the access token
    return Token(access_token=access_token, token_type="bearer")


@router.get("/password_analysis")
def get_password_analysis(
    password: str, email: EmailStr, username: UsernameStr
) -> Dict[str, Any]:
    """
    Analyses a password, given the password, the user's email address and the user's username.
    Also returns a strong_enough key.
    This is directy used by POST /users/ to verify password strength.
    You can thus use this to give feedback to the user before submitting.
    """
    if (analysis := analyze_password(password, email, username)) is None:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while analyzing the password",
        )
    analysis = make_json_serializable(analysis)
    del analysis["password"]
    analysis["strong_enough"] = is_password_strong_enough(analysis)
    return analysis
