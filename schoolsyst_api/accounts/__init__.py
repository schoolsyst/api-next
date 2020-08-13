import os
from datetime import datetime, timedelta
from typing import Optional

from arango.database import StandardDatabase
from fastapi_utils.inferring_router import InferringRouter
from jose import jwt
from schoolsyst_api.models import DBUser

JWT_SIGN_ALGORITHM = "HS256"


def get_user(db: StandardDatabase, username: str) -> Optional[DBUser]:
    """
    Get a user by username from the DB.
    Returns `None` if the user is not found.
    """
    # Usernames are not case-sensitive
    user_dict = db.collection("users").find({"username": username.lower()}).batch()
    if not user_dict:
        return None
    return DBUser(**user_dict[0])


def create_jwt_token(sub_format: str, sub_value: str, valid_for: timedelta) -> str:
    return jwt.encode(
        {"sub": sub_format.format(sub_value), "exp": datetime.utcnow() + valid_for},
        key=os.getenv("SECRET_KEY"),
        algorithm=JWT_SIGN_ALGORITHM,
    )


def verify_jwt_token(token: str, sub_format: str, sub_value: str) -> bool:
    try:
        jwt.decode(
            token,
            key=os.getenv("SECRET_KEY"),
            algorithms=[JWT_SIGN_ALGORITHM],
            subject=sub_format.format(sub_value),
        )
    except (jwt.JWTError, jwt.JWTClaimsError, jwt.ExpiredSignatureError):
        return False
    return True


router = InferringRouter()
