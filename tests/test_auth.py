from fastapi.testclient import TestClient
from schoolsyst_api.main import api

client = TestClient(api)


def test_read_users_self_not_logged_in():
    # Try to access user without logging in
    response = client.get("/users/self")
    assert response.status_code == 401


def test_read_users_self_logged_in():
    # login
    client.post("/auth", {"username": "alice", "password": "uhuihihiuhiuhuihui"})
