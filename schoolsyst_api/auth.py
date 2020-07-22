import os
from datetime import datetime, time, timedelta
from typing import *
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from schoolsyst_api import models

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
        "password_hash": "$argon2id$v=19$m=102400,t=2,p=8$FQJgLCVEKMU4R6i1tlbqXQ$A9GkJWjats+p11hO/l17Mg",
        "email_is_confirmed": True,
    },
}

api = FastAPI()


def fake_hash_password(password: str):
    return "fakehashed" + password


load_dotenv("../.env")
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_SIGN_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


password_context = CryptContext(schemes=["argon2"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)


def hash_password(plain_password: str) -> str:
    return password_context.hash(plain_password)


def get_user(
    fake_db: Dict[str, Dict[str, Any]], username: str
) -> Optional[models.DBUser]:
    user_dict = fake_db.get(username)
    if not user_dict:
        return None
    return models.DBUser(**user_dict)


def authenticate_user(fake_db: Dict[str, Dict[str, Any]], username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta is not None else timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_SIGN_ALGORITHM)
    return encoded_jwt


def extract_username_from_jwt_payload(payload: dict) -> Optional[str]:
    if (subject := payload.get("sub")) is None:
        return None
    if not subject.startswith("username:"):
        return None
    else:
        return subject[len("username:") :]


async def get_current_user(token: str = Depends(oauth2_scheme)):
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
        token_data = TokenData(username=username)
    except JWTError:
        # If any kind of JWT-related error happened
        raise credentials_exception
    # Get the user from the database. At this step token_data.username is not None.
    user = get_user(fake_users_db, username=token_data.username)
    # If the token's payload refers to an unknown user
    if user is None:
        raise credentials_exception
    # Finally return the user
    # get_user actually returns DBUser, which contains the password hash, 
    # we don't want this in the public output.
    return models.User(**user.dict())


async def get_current_confirmed_user(
    current_user: models.User = Depends(get_current_user),
):
    if not current_user.email_is_confirmed:
        raise HTTPException(
            status_code=400, detail="User has not confirmed its email address"
        )
    return current_user


@api.get("/users/self", response_model=models.User)
async def read_users_self(
    current_user: models.User = Depends(get_current_confirmed_user),
):
    return current_user


@api.post("/auth/")
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
        data={"sub": f"username:{user.username}"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    # Return the access token
    return {"access_token": access_token, "token_type": "bearer"}
