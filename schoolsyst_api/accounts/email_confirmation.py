import os
from datetime import timedelta

from arango.database import StandardDatabase
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, status
from schoolsyst_api import database
from schoolsyst_api.accounts import router
from schoolsyst_api.accounts.models import User
from schoolsyst_api.accounts.users import get_current_user
from schoolsyst_api.email_confirmed_action import EmailConfirmedAction

load_dotenv(".env")
SECRET_KEY = os.getenv("SECRET_KEY")
VALID_FOR = timedelta(hours=24)

helper = EmailConfirmedAction(
    name="email_confirmation",
    callback_url="https://app.schoolsyst.com/confirm_email/{}/",
    token_valid_for=VALID_FOR,
    email_subject="schoolsyst: Confirmation d'email - {}",
)


@router.post(
    "/email_confirmation/request",
    summary="Request an email confirmation",
    description=f"""
Sends an email to the logged-in user's email address,
and creates a `EmailConfirmationRequest` with a temporary token,
The email can then be confirmed with `POST /users/email-confirmation/`.

The token is considered expired {VALID_FOR.total_seconds() / 3600} hours after creation.
    """.strip(),
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_users_password_reset_request(
    tasks: BackgroundTasks, user: User = Depends(get_current_user),
):
    helper.send_request(current_user=user, tasks=tasks)
    return


post_users_email_confirmation_responses = {
    403: {
        "description": "The token is either corrupted, emitted by another user or expired"
    },
}


@router.post(
    "/email_confirmation",
    summary="Confirm an email",
    responses=post_users_email_confirmation_responses,
)
async def post_users_password_reset(
    token: str,
    user: User = Depends(get_current_user),
    db: StandardDatabase = Depends(database.get),
):
    """
    Confirms the user's email address given a `token`.

    The `token` is a token sent to the user's email address as a link
    (something like `https://app.schoolsyst.com/email-confirmation/{request_token}`)
    after performing a `POST /users/email-confirmation-request`.
    """
    # verify the token
    helper.handle_token_verification(token, user)
    # confirm the email
    db.collection("users").update({"_key": user.key, "email_is_confirmed": True})
    return {}
