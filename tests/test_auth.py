import json
import os
from datetime import datetime

from arango.database import StandardDatabase
from fastapi import status
from fastapi.testclient import TestClient
from isodate import isodatetime
from schoolsyst_api.main import api
from schoolsyst_api.models import DBUser, User
from schoolsyst_api.users import hash_password
from tests import authed_request, database_mock

os.environ["TESTING"] = "True"
client = TestClient(api)
ALICE_PASSWORD = "fast-unicorn-snails-dragon5"


class mocks:
    class users:
        alice = DBUser(
            _key="fea7d52d-8b1f-406b-a23a-98fcb000a0c7",
            username="alice",
            password_hash=hash_password(ALICE_PASSWORD),
            joined_at=datetime(2020, 7, 23, 22, 41, 0),
            email="hey@alice.example.com",
        )


def test_read_users_self_not_logged_in():
    with database_mock() as db:
        db.collection("users").insert(mocks.users.alice.json(by_alias=True))
        # Try to access user without logging in
        response = client.get("/users/self")
        assert response.status_code == 401


def test_auth():
    # login
    with database_mock() as mock:
        mock.collection("users").insert(mocks.users.alice.json(by_alias=True))
        response = client.post(
            "/auth/",
            data={"username": mocks.users.alice.username, "password": ALICE_PASSWORD},
        )
        assert response.status_code == 200
        assert "access_token" in response.json().keys()
        assert "token_type" in response.json().keys()


def test_read_users_self_logged_in():
    with database_mock() as db:
        db.collection("users").insert(mocks.users.alice.json(by_alias=True))

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get("/users/self/", **params)

        assert response.status_code == 200
        assert response.json() == json.loads(
            User(**mocks.users.alice.dict(by_alias=True)).json(by_alias=True)
        )


def test_create_user_ok():
    with database_mock() as db:
        assert db.collection("users").all().count() == 0

        response = client.post(
            "/users/",
            json={
                "username": mocks.users.alice.username,
                "password": ALICE_PASSWORD,
                "email": mocks.users.alice.email,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["username"] == mocks.users.alice.username
        assert response.json()["email"] == mocks.users.alice.email
        assert not response.json()["email_is_confirmed"]
        joined_at = isodatetime.parse_datetime(response.json()["joined_at"])
        assert joined_at.today
        assert "_key" in response.json().keys()


def test_create_user_username_disallowed():
    with database_mock() as db:
        assert db.collection("users").all().count() == 0

        response = client.post(
            "/users/",
            json={
                "username": "admin",
                "password": ALICE_PASSWORD,
                "email": mocks.users.alice.email,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username is not allowed" in response.json()["detail"]


def test_create_user_username_taken():
    with database_mock() as db:
        db: StandardDatabase
        db.collection("users").insert(mocks.users.alice.json(by_alias=True))

        response = client.post(
            "/users/",
            json={
                "username": mocks.users.alice.username,
                "password": ALICE_PASSWORD,
                "email": "alice@gmail.com",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username is already taken" in response.json()["detail"]


def test_create_user_email_taken():
    with database_mock() as db:
        db: StandardDatabase
        db.collection("users").insert(mocks.users.alice.json(by_alias=True))

        response = client.post(
            "/users/",
            json={
                "username": "john",
                "password": ALICE_PASSWORD,
                "email": mocks.users.alice.email,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email is already taken" in response.json()["detail"]


def test_create_user_password_too_simple():
    with database_mock() as db:
        assert db.collection("users").all().count() == 0

        response = client.post(
            "/users/",
            json={
                "username": mocks.users.alice.username,
                "password": "hunter2",
                "email": mocks.users.alice.email,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password is not strong enough" in response.json()["detail"]["message"]
        assert "analysis" in response.json()["detail"].keys()


def test_password_analysis():
    # We don't test extensively,
    # it's up to python-zxcvbn to test their own library.
    response = client.get(
        "/password-analysis/",
        params={
            "password": "hunter2",
            "email": "whatever@itdoesntcountforth.is",
            "username": "no_u",
        },
    )

    assert response.status_code == 200
    assert "password" not in response.json().keys()
    assert "strong_enough" in response.json().keys()
    assert not response.json()["strong_enough"]
