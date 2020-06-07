import os
from datetime import timedelta

from jose import jwt
from schoolsyst_api.accounts.email_confirmation import (
    JWT_SUB_FORMAT,
    create_email_confirmation_request_token,
)


def test_create_email_confirmation_request_token():
    token = create_email_confirmation_request_token("ewen-lbh", timedelta(hours=24))
    decoded = jwt.decode(
        token, key=os.getenv("SECRET_KEY"), subject=JWT_SUB_FORMAT.format("ewen-lbh")
    )
    assert decoded
