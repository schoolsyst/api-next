from datetime import datetime, timedelta
from os import getenv
from time import sleep

from arango.database import StandardDatabase
from jose import jwt
from schoolsyst_api.accounts import (
    JWT_SIGN_ALGORITHM,
    create_jwt_token,
    get_user,
    verify_jwt_token,
)
from tests import database_mock, mocks


def test_get_user():
    with database_mock() as db:
        db: StandardDatabase
        db.collection("users").insert(mocks.users.john.json(by_alias=True))
        assert get_user(db, mocks.users.john.username) == mocks.users.john
        assert get_user(db, "hmmmmmm") is None


def test_create_jwt_token():
    token = create_jwt_token("lorem:{}", "ipsum", timedelta(24, 20, 10))
    decoded = jwt.decode(token, getenv("SECRET_KEY"), algorithms=JWT_SIGN_ALGORITHM)
    assert decoded["sub"] == "lorem:ipsum"
    # the code will take less than one second to execute, so it's okay
    assert decoded["exp"] == int((datetime.now() + timedelta(24, 20, 10)).timestamp())


def test_verify_jwt_token():
    token = create_jwt_token("lorem:{}", "ipsum", timedelta(seconds=1))
    assert verify_jwt_token(token, "lorem:{}", "ipsum")
    assert not verify_jwt_token(token, "loram:{}", "ipsum")
    assert not verify_jwt_token(token, "lorem:{}", "ipsumeee")
    assert not verify_jwt_token(token, "loreem:{}", "ipsumeee")
    sleep(2)
    assert not verify_jwt_token(token, "lorem:{}", "ipsum")
    assert not verify_jwt_token(token, "loram:{}", "ipsum")
    assert not verify_jwt_token(token, "lorem:{}", "ipsumeee")
    assert not verify_jwt_token(token, "loreem:{}", "ipsumeee")
