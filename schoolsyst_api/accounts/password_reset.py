import os
from datetime import datetime, timedelta

from arango.database import StandardDatabase
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from schoolsyst_api import database
from schoolsyst_api.accounts import create_jwt_token, router, verify_jwt_token
from schoolsyst_api.accounts.auth import (
    analyze_a_password,
    hash_password,
    is_password_strong_enough,
)
from schoolsyst_api.accounts.models import User
from schoolsyst_api.accounts.users import get_current_confirmed_user
from schoolsyst_api.models import UserKey

load_dotenv(".env")
SECRET_KEY = os.getenv("SECRET_KEY")
VALID_FOR = timedelta(minutes=30)
JWT_SUB_FORMAT = "password-reset:{}"


class PasswordResetRequest(BaseModel):
    created_at: datetime
    token: str
    emitted_by_key: UserKey


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

The token is considered expired {VALID_FOR.total_seconds()} seconds after creation,
and the `PasswordResetRequest` is destroyed once an associated
`POST /users/password-reset` is made.

In other words, the request is valid for up to {VALID_FOR.total_seconds()} seconds,
and can only be used once.
    """.strip(),
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_users_password_reset_request(
    tasks: BackgroundTasks, user: User = Depends(get_current_confirmed_user),
):
    # create a request
    token = create_jwt_token(JWT_SUB_FORMAT, user.username, VALID_FOR)

    # send an email
    tasks.add_task(send_password_reset_email, user.email, user.username, token)
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
    # validate the token
    if not verify_jwt_token(change_data.request_token, JWT_SUB_FORMAT, user.username):
        return HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail=post_users_password_reset_responses[403]["description"],
        )
    # change the password
    db.collection("users").update(
        {"_key": user.key, "password_hash": hash_password(change_data.new_password)}
    )
    return
