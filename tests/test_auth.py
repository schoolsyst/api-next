import os
from datetime import datetime

from fastapi.testclient import TestClient
from schoolsyst_api.main import api
from schoolsyst_api.models import DBUser
from schoolsyst_api.users import hash_password
from tests import database_mock

os.environ["TESTING"] = "True"
client = TestClient(api)


class mocks:
    class users:
        alice = DBUser(
            _key="fea7d52d-8b1f-406b-a23a-98fcb000a0c7",
            username="alice",
            password_hash=hash_password("uhuihihiuhiuhuihui"),
            joined_at=datetime(2020, 7, 23, 22, 41, 0),
            email="hey@alice.example.com",
        )


def test_read_users_self_not_logged_in():
    with database_mock() as db:
        db.collection("users").insert(mocks.users.alice.json(by_alias=True))
        # Try to access user without logging in
        response = client.get("/users/self")
        assert response.status_code == 401


def test_read_users_self_logged_in():
    # login
    with database_mock() as mock:
        mock.collection("users").insert(mocks.users.alice.json(by_alias=True))
        response = client.post(
            "/auth/",
            data={
                "username": mocks.users.alice.username,
                "password": "uhuihihiuhiuhuihui",
            },
        )
        assert response.status_code == 200
        assert "access_token" in response.json().keys()
        assert "token_type" in response.json().keys()
