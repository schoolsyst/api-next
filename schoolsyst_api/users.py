import os
from datetime import datetime, timedelta
from os import stat
from smtplib import SMTP, SMTP_SSL_PORT
from typing import *
from uuid import uuid4

from arango.database import StandardDatabase
from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from parse import parse
from passlib.context import CryptContext
from pydantic import UUID4, BaseModel, EmailStr
from schoolsyst_api import database
from schoolsyst_api.models import DBUser, User, UserCreation

router = APIRouter()

fake_users_db = {
    "johndoe": {
        "uuid": uuid4(),
        "joined_at": datetime.now(),
        "username": "johndoe",
        "email": "johndoe@example.com",
        "password_hash": "$argon2id$v=19$m=102400,t=2,p=8$JQTg/B/jvJeSkhKCEKLUug$u28ihCrLS7tAXAhV7KWRoQ",
        "email_is_confirmed": False,
    },
    "alice": {
        "uuid": uuid4(),
        "joined_at": datetime.now(),
        "username": "alice",
        "email": "alice@example.com",
        "password_hash": "$argon2id$v=19$m=102400,t=2,p=8$8J5TKqUUIuT8f885J2Rs7Q$iCk+iO81x9OzuR7bTAJrTw",
        "email_is_confirmed": True,
    },
}

load_dotenv(".env")
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_SIGN_ALGORITHM = "HS256"
JWT_SUB_FORMATS = {
    "user": "username:{}",
    "password reset": "password-reset:{}",
}
ACCESS_TOKEN_EXPIRE_MINUTES = 30
PASSWORD_REQUEST_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    """As defined by OAuth 2"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Models the data in the JWT token's payload"""

    username: Optional[str] = None


# Context for password hashing
password_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Special FastAPI class to inject as a dependency
# and get appropriate openapi.json integration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that the plain_password matches against a hash `hashed_password`

    >>> verify_password("correct-battery-horse-staple", "$argon2id$v=19$m=102400,t=2,p=8$h/Bea41xjlEqBQAgpPTemw$tprEaXUjIeEP+B9ryxSVAw")
    True
    >>> verify_password("correct-battery-horse-staple", "$argon2id$v=19$m=102400,t=2,p=8$h/Bea41xjlEqBQAgpkTemw$tprEaXUjIeEP+B9ryxSVAw")
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


def get_user(db: StandardDatabase, username: str) -> Optional[DBUser]:
    """
    Get a user by username from the DB.
    Returns `None` if the user is not found.
    """
    # Usernames are not case-sensitive
    user_dict = db.collection("users").get(username)
    if not user_dict:
        return None
    return DBUser(**user_dict)


def is_username_taken(db: StandardDatabase, username: str) -> bool:
    """
    Checks if the given username is already taken
    """
    return db.collection("users").find({"username": username}).count() > 0


def is_email_taken(db: StandardDatabase, email: EmailStr) -> bool:
    """
    Checks if the given email is already taken
    """
    return db.collection("users").find({"email": email}).count() > 0


def authenticate_user(db: StandardDatabase, username: str, password: str):
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


def create_access_token(payload: dict, expires_delta: timedelta):
    """
    Creates an OAuth2 JWT access token:
    Encodes the `payload` with SECRET_KEY using JWT_SIGN_ALGORITHM,
    set the expiration timestamp `exp` to `expires_delta` in the future

    >>> create_access_token(
    ...     {"sub": "cruise"},
    ...     timedelta(seconds=50)
    ... ).startswith('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9')
    True
    """
    key = os.getenv("SECRET_KEY")
    if not key:
        raise ValueError("SECRET_KEY must be set in .env")
    to_encode = payload.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, key, algorithm=JWT_SIGN_ALGORITHM)
    return encoded_jwt


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
    >>> extract_username_from_jwt_payload({})
    """
    if (subject := payload.get("sub")) is None:
        return None
    if (username := parse(JWT_SUB_FORMATS["user"], subject)) is None:
        return None
    return username[0]


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get the current user from `oauth2_scheme`'s token.
    The (JWT) token is decoded, the username is extracted from its payload,
    then the user is looked up by username from the database and returned.

    For security concerns, the pydantic model returned does not include the password hash.

    A 401 Unauthorized exception is automatically raised if any problem arises
    during token decoding or user lookup
    """
    db = database.initialize()
    # exception used everytime an error is encountered during verification
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Try to decode the jwt token and get the payload's sub
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_SIGN_ALGORITHM])
        username = extract_username_from_jwt_payload(payload)
        # In that case the jwt token is invalid
        if username is None:
            raise credentials_exception
        # Store the token data here (in case we have more data to store in the playload)
        print("./schoolsyst_api/users.py:204 => username")
        print("\t" + repr(username))
        token_data = TokenData(username=username)
    except JWTError:
        # If any kind of JWT-related error happened
        raise credentials_exception
    # Get the user from the database. At this step token_data.username is not None.
    user = get_user(db, username=token_data.username)
    # If the token's payload refers to an unknown user
    if user is None:
        raise credentials_exception
    # Finally return the user
    # get_user actually returns DBUser, which contains the password hash,
    # we don't want this in the public output.
    return User(**user.dict())


async def get_current_confirmed_user(current_user: User = Depends(get_current_user),):
    """
    Gets the current user with `get_current_user` and raises a 400 if the gotten user
    hasn't confirmed its email address
    """
    if not current_user.email_is_confirmed:
        raise HTTPException(
            status_code=400, detail="User has not confirmed its email address"
        )
    return current_user


@router.get(
    "/users/self", response_model=User, summary="Get the currently logged-in user",
)
async def read_users_self(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/auth/", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Try to auth the user
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Create the access token
    access_token = create_access_token(
        payload={"sub": f"username:{user.username}"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    # Return the access token
    return Token(access_token=access_token, token_type="bearer")


post_users_error_responses = {
    400: {
        "description": "This username is already taken | This email is already taken."
    }
}


@router.post(
    "/users/",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user account",
    responses=post_users_error_responses,
)
def create_user_account(
    user_in: UserCreation, db: StandardDatabase = Depends(database.initialize)
):
    """
    Create a user account.
    Emails and usernames are unique, usernames are _not_ case-sensitive
    """
    # Check if the username is not already taken
    if is_username_taken(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken",
        )
    # Check if the email is not already taken
    if is_email_taken(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already taken",
        )
    # Create the DBUser
    db_user = DBUser(
        _key=uuid4(),
        joined_at=datetime.utcnow(),
        email_is_confirmed=False,
        password_hash=hash_password(user_in.password),
        **user_in.dict(),
    )
    db.collection("users").insert(db_user.json(by_alias=True))
    # Return a regular User
    return User(**db_user.dict(by_alias=True))


class PasswordResetRequest(BaseModel):
    created_at: datetime
    token: str
    emitted_by_id: UUID4


def create_password_reset_request_token(
    username: str, request_valid_for: timedelta
) -> str:
    return jwt.encode(
        {
            "sub": JWT_SUB_FORMATS["password reset"].format(username),
            "exp": datetime.utcnow() + request_valid_for,
        },
        SECRET_KEY,
        algorithm=JWT_SIGN_ALGORITHM,
    )


def send_password_reset_email(
    to_email: str, to_username: str, password_reset_request_token: str
) -> bool:
    email = f"""\
From: schoolsyst password reset system <reset-password@schoolsyst.com>
To: {to_username} <{to_email}>
Subject: Reset your schoolsyst password

Go to https://app.schoolsyst.com/reset-password/{password_reset_request_token} to reset it.
If you didn't request a password reset, just ignore this, and your password won't be modified.
"""
    print("[fake] sending email:")
    print("---")
    print(email)
    print("---")
    # host = SMTP("email.schoolsyst.com", SMTP_SSL_PORT, "localhost")
    # host.sendmail(
    #     from_addr="reset-password@schoolsyst.com",
    #     to_addrs=[to_email],
    #     msg=email,
    # )
    return True


@router.post(
    "/users/password-reset-request",
    summary="Request a password reset",
    description=f"""
Sends an email to the logged-in user's email address,
and creates a `PasswordResetRequest` with a temporary token,
A new password can then be set with `POST /users/password-reset/`.

The token is considered expired {PASSWORD_REQUEST_TOKEN_EXPIRE_MINUTES} minutes after creation,
and the `PasswordResetRequest` is destroyed once an associated
`POST /users/password-reset` is made.

In other words, the request is valid for up to {PASSWORD_REQUEST_TOKEN_EXPIRE_MINUTES} minutes,
and can only be used once.
    """.strip(),
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_users_password_reset_request(
    tasks: BackgroundTasks, user: User = Depends(get_current_confirmed_user)
):
    # create a request
    request = PasswordResetRequest(
        created_at=datetime.utcnow(),
        emitted_by_id=user.uuid,
        token=create_password_reset_request_token(
            user.username,
            request_valid_for=timedelta(minutes=PASSWORD_REQUEST_TOKEN_EXPIRE_MINUTES),
        ),
    )
    # send an email
    tasks.add_task(send_password_reset_email, user.email, user.username, request.token)
    return


class PasswordReset(BaseModel):
    request_token: str
    new_password: str


post_users_password_reset_responses = {
    403: {
        "description": "The token is either corrupted, emitted by another user or expired"
    }
}


@router.post(
    "/users/password-reset",
    summary="Reset a password",
    responses=post_users_password_reset_responses,
)
async def post_users_password_reset(
    change_data: PasswordReset, user: User = Depends(get_current_confirmed_user),
):
    """
    Changes the password given a `request_token`.

    The `request_token` is a token sent to the user's email address as a link
    (something like `https://app.schoolsyst.com/password-reset/{request_token}`) after
    performing a `POST /users/password-reset-request`.
    """
    http_error = HTTPException(
        status.HTTP_403_FORBIDDEN,
        detail=post_users_password_reset_responses[403]["description"],
    )
    # check if change_data.request_token actually exists
    password_reset_requests: List[PasswordResetRequest] = []
    matching_requests = [
        r for r in password_reset_requests if r.token == change_data.request_token
    ]
    # duplicate tokens should never occur, but, just in case, we consider the token as "not found"
    if not matching_requests or len(matching_requests) > 1:
        raise http_error
    # check if its associated with the current user
    matching_request = matching_requests[0]
    if matching_request.emitted_by_id != user.uuid:
        raise http_error
    # check if the token isn't expired
    try:
        token_payload = jwt.decode(
            matching_requests.token, SECRET_KEY, algorithms=[JWT_SIGN_ALGORITHM]
        )
        expiration_datetime = datetime.fromtimestamp(token_payload.get("exp"))
        expired = expiration_datetime < datetime.now()
    except JWTError:
        raise http_error
    except KeyError:
        raise http_error
    if expired:
        raise http_error
    # change the password
    return
