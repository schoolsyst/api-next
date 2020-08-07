import os
from datetime import datetime, timedelta

from arango.database import StandardDatabase
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel
from schoolsyst_api import database
from schoolsyst_api.accounts import router
from schoolsyst_api.accounts.users import get_current_user
from schoolsyst_api.models import User, UserKey

load_dotenv(".env")
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_SIGN_ALGORITHM = "HS256"
EMAIL_CONFIRMATION_REQUEST_TOKEN_EXPIRE_HOURS = 24
JWT_SUB_FORMAT = "email-confirmation:{}"
JWT_SIGN_ALGORITHM = "HS256"


def send_email_confirmation_email(
    to_email: str, to_username: str, email_confirm_request_token: str
) -> bool:
    email = f"""\
From: schoolsyst password reset system <reset-password@schoolsyst.com>
To: {to_username} <{to_email}>
Subject: Confirm your email address

Go to https://app.schoolsyst.com/email-confirm/{email_confirm_request_token} to confirm your email address.
If you didn't request an email confirmation or don't know what schoolsyst is,
this means that someone tried to register an account and/or confirm an email address using
yours instead of theirs. Just ignore this and your email address won't be confirmed.
If you have any reason to think that this person has access to your mailbox, you may change your
email account's password.
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


class EmailConfirmationRequest(BaseModel):
    created_at: datetime
    token: str
    emitted_by_key: UserKey


def create_email_confirmation_request_token(
    username: str, request_valid_for: timedelta
) -> str:
    return jwt.encode(
        {
            "sub": JWT_SUB_FORMAT.format(username),
            "exp": datetime.utcnow() + request_valid_for,
        },
        SECRET_KEY,
        algorithm=JWT_SIGN_ALGORITHM,
    ).decode("utf-8")


@router.post(
    "/users/email-confirmation-request",
    summary="Request an email confirmation",
    description=f"""
Sends an email to the logged-in user's email address,
and creates a `EmailConfirmationRequest` with a temporary token,
The email can then be confirmed with `POST /users/email-confirmation/`.

The token is considered expired {EMAIL_CONFIRMATION_REQUEST_TOKEN_EXPIRE_HOURS} minutes after creation,
and the `EmailConfirmationRequest` is destroyed once an associated
`POST /users/email-confirmation` is made.

In other words, the request is valid for up to {EMAIL_CONFIRMATION_REQUEST_TOKEN_EXPIRE_HOURS} minutes,
and can only be used once.
    """.strip(),
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_users_password_reset_request(
    tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: StandardDatabase = Depends(database.get),
):
    # create a request
    request = EmailConfirmationRequest(
        created_at=datetime.utcnow(),
        emitted_by_key=user.key,
        token=create_email_confirmation_request_token(
            user.username,
            request_valid_for=timedelta(
                hours=EMAIL_CONFIRMATION_REQUEST_TOKEN_EXPIRE_HOURS
            ),
        ),
    )
    # store it
    db.collection("email_confirmation_requests").insert(request.json(by_alias=True))

    # send an email
    tasks.add_task(
        send_email_confirmation_email, user.email, user.username, request.token
    )
    return


post_users_email_confirmation_responses = {
    403: {
        "description": "The token is either corrupted, emitted by another user or expired"
    },
}


@router.post(
    "/users/email-confirmation",
    summary="Confirm an email",
    responses=post_users_email_confirmation_responses,
)
async def post_users_password_reset(
    token: str,
    user: User = Depends(get_current_user),
    db: StandardDatabase = Depends(database.get),
):
    """
    Confirms the user's email address given a `request_token`.

    The `request_token` is a token sent to the user's email address as a link
    (something like `https://app.schoolsyst.com/email-confirmation/{request_token}`)
    after performing a `POST /users/email-confirmation-request`.
    """
    http_error = HTTPException(
        status.HTTP_403_FORBIDDEN,
        detail=post_users_email_confirmation_responses[403]["description"],
    )
    # check if change_data.request_token actually exists
    matching_requests = (
        db.collection("email_confirmation_requests").find({"token": token}).batch()
    )
    # duplicate tokens should never occur, but, just in case, we consider the token as "not found"
    if not matching_requests or len(matching_requests) > 1:
        raise http_error
    # check if its associated with the current user
    matching_request = EmailConfirmationRequest(**matching_requests[0])
    if matching_request.emitted_by_key != user.key:
        raise http_error
    # check if the token isn't expired
    try:
        token_payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_SIGN_ALGORITHM])
        expiration_datetime = datetime.fromtimestamp(token_payload.get("exp"))
        expired = expiration_datetime < datetime.now()
    except JWTError:
        raise http_error
    except KeyError:
        raise http_error
    if expired:
        raise http_error
    # confirm the email
    db.collection("users").update({"_key": user.key, "email_is_confirmed": True})
    return {}
