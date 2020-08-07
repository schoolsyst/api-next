from typing import Optional

from arango.database import StandardDatabase
from fastapi.routing import APIRouter
from schoolsyst_api.models import DBUser


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


router = APIRouter()
