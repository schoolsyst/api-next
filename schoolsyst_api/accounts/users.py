import os
from datetime import datetime
from pathlib import Path

from arango.database import StandardDatabase
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from pydantic import EmailStr
from schoolsyst_api import database
from schoolsyst_api.accounts import get_user, router
from schoolsyst_api.accounts.auth import (
    TokenData,
    analyze_a_password,
    extract_username_from_jwt_payload,
    hash_password,
    is_password_strong_enough,
    oauth2_scheme,
)
from schoolsyst_api.accounts.models import DBUser, InUser, User
from schoolsyst_api.database import COLLECTIONS

load_dotenv(".env")
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_SIGN_ALGORITHM = "HS256"

# Load the list of disallowed usernames
DISALLOWED_USERNAMES = (
    (Path(__file__).parent / "disallowed_usernames.txt").read_text().splitlines()
)


def is_username_disallowed(username: str) -> bool:
    return username in DISALLOWED_USERNAMES


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


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: StandardDatabase = Depends(database.get)
) -> User:
    """
    Dependency to get the current user from `oauth2_scheme`'s token.
    The (JWT) token is decoded, the username is extracted from its payload,
    then the user is looked up by username from the database and returned.

    For security concerns, the pydantic model returned
    does not include the password hash.

    A 401 Unauthorized exception is automatically raised if any problem arises
    during token decoding or user lookup
    """
    # exception used everytime an error is encountered during verification
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Try to decode the jwt token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_SIGN_ALGORITHM])
    except JWTError:
        # If any kind of JWT-related error happened
        raise credentials_exception
    # Get the username from the decoded jwt token
    username = extract_username_from_jwt_payload(payload)
    # In that case the jwt token is invalid
    if username is None:
        raise credentials_exception
    # Store the token data in TokenData
    print("./schoolsyst_api/users.py:83 => username")
    print("\t" + repr(username))
    token_data = TokenData(username=username)
    # Get the user from the database. At this step token_data.username is not None.
    user = get_user(db, username=token_data.username)
    # If the token's payload refers to an unknown user
    if user is None:
        raise credentials_exception
    # Finally return the user
    # get_user actually returns DBUser, which contains the password hash,
    # we don't want this in the public output.
    return User(**user.dict(by_alias=True))


async def get_current_confirmed_user(
    current_user: User = Depends(get_current_user),
) -> User:
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
    "/users/self", summary="Get the currently logged-in user",
)
async def read_users_self(current_user: User = Depends(get_current_user)) -> User:
    return current_user


post_users_error_responses = {
    400: {
        "description": "This username is already taken"
        " | This email is already taken"
        " | The password is not strong enough"
        " | This username is not allowed"
    }
}


@router.post(
    "/users/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a user account",
    responses=post_users_error_responses,
)
def create_user_account(
    user_in: InUser, db: StandardDatabase = Depends(database.get)
) -> User:
    """
    Create a user account.
    Emails and usernames are unique, usernames are _not_ case-sensitive.
    The password must be strong enough. See GET /password-analysis/
    """
    # Check if the username is not disallowed
    if is_username_disallowed(user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is not allowed.",
        )
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
    # Check if password is strong enough
    password_analysis = analyze_a_password(**user_in.dict())
    if password_analysis and not is_password_strong_enough(password_analysis):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "The password is not strong enough",
                "analysis": password_analysis,
            },
        )
    # Create the DBUser
    db_user = DBUser(
        joined_at=datetime.utcnow(),
        email_is_confirmed=False,
        password_hash=hash_password(user_in.password),
        **user_in.dict(),
    )
    db.collection("users").insert(db_user.json(by_alias=True))
    # Return a regular User
    return User(**db_user.dict(by_alias=True))


@router.delete("/users/self")
async def delete_currently_logged_in_user(
    user: User = Depends(get_current_user),
    really_delete: bool = False,
    db: StandardDatabase = Depends(database.get),
):
    """
    Deletes the currently-logged-in user, and all of the associated resources.
    This action does not require the user to have confirmed its email address.
    """
    if not really_delete:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set really_delete to True to confirm deletion",
        )

    db.collection("users").delete(user.key)
    for c in COLLECTIONS:
        if c == "users":
            continue

        db.collection(c).delete_match({"owner_key": user.key})


@router.get("/all-personal-data")
async def get_all_personal_data(
    user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
) -> dict:
    """
    Get an archive of all of the data linked to the user.
    """
    data = {}
    # The user's data
    data["user"] = db.collection("users").get(user.key)
    # the data of which the user is the owner for every collection
    for c in COLLECTIONS:
        if c == "users":
            continue
        data[c] = [batch for batch in db.collection(c).find({"owner_key": user.key})]
    return data
