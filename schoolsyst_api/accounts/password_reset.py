import os
from datetime import datetime, timedelta
from typing import List

from arango.database import StandardDatabase
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel
from schoolsyst_api import database
from schoolsyst_api.accounts import router
from schoolsyst_api.accounts.auth import (
    analyze_a_password,
    hash_password,
    is_password_strong_enough,
)
from schoolsyst_api.accounts.users import get_current_confirmed_user
from schoolsyst_api.models import User, UserKey

load_dotenv(".env")
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_SIGN_ALGORITHM = "HS256"
PASSWORD_REQUEST_TOKEN_EXPIRE_MINUTES = 30
JWT_SUB_FORMAT = "password-reset:{}"


class PasswordResetRequest(BaseModel):
    created_at: datetime
    token: str
    emitted_by_key: UserKey


def create_password_reset_request_token(
    username: str, request_valid_for: timedelta
) -> str:
    return jwt.encode(
        {
            "sub": JWT_SUB_FORMAT.format(username),
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
    tasks: BackgroundTasks,
    user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
):
    # create a request
    request = PasswordResetRequest(
        created_at=datetime.utcnow(),
        emitted_by_key=user.key,
        token=create_password_reset_request_token(
            user.username,
            request_valid_for=timedelta(minutes=PASSWORD_REQUEST_TOKEN_EXPIRE_MINUTES),
        ),
    )
    # store it
    db.collection("password_reset_requests").insert(request.json(by_alias=True))

    # send an email
    tasks.add_task(send_password_reset_email, user.email, user.username, request.token)
    return


class PasswordReset(BaseModel):
    request_token: str
    new_password: str


post_users_password_reset_responses = {
    403: {
        "description": "The token is either corrupted, emitted by another user or expired"
    },
    400: {"description": "This password is not strong enough"},
}


@router.post(
    "/users/password-reset",
    summary="Reset a password",
    responses=post_users_password_reset_responses,
)
async def post_users_password_reset(
    change_data: PasswordReset,
    user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
):
    """
    Changes the password given a `request_token`.

    The `request_token` is a token sent to the user's email address as a link
    (something like `https://app.schoolsyst.com/password-reset/{request_token}`) after
    performing a `POST /users/password-reset-request`.
    """
    analysis = analyze_a_password(change_data.new_password, user.email, user.username)
    if analysis and not is_password_strong_enough(analysis):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password is not strong enough",
            headers={"X-See": "GET /password-analysis/"},
        )
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
    if matching_request.emitted_by_key != user.key:
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
    new_password_hash = hash_password(change_data.new_password)
    db.collection("users").update(
        {"_key": user.key, "password_hash": new_password_hash}
    )
    return
