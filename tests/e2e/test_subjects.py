import json

from arango.database import StandardDatabase
from fastapi import status
from tests import authed_request, client, database_mock, insert_mocks, mocks
from tests.mocks import ALICE_PASSWORD


def test_list_subjects():
    with database_mock() as db:
        db: StandardDatabase

        assert db.collection("subjects").all().count() == 0
        insert_mocks(db, "users")
        insert_mocks(db, "subjects")

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get("/subjects/", **params)
            keys = [s["_key"] for s in response.json()]

            assert response.status_code == 200
            assert len(response.json()) == 2
            assert mocks.subjects.sciences_de_l_ingénieur._key not in keys
            assert all(
                [
                    s._key in keys
                    for s in (mocks.subjects.français, mocks.subjects.mathematiques)
                ]
            )


def test_read_subject_not_authed():
    with database_mock():
        response = client.get("/subjects/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_read_subject_not_found():
    with database_mock() as db:
        db: StandardDatabase

        insert_mocks(db, "users")
        db.collection("subjects").insert(mocks.subjects.mathematiques.json())

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get(
                f"/subjects/{mocks.subjects.français.object_key}/", **params
            )
            assert response.status_code == 404


def test_read_subject_not_owned_by_current_user():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        db.collection("subjects").insert(mocks.subjects.sciences_de_l_ingénieur.json())

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get(
                f"/subjects/{mocks.subjects.sciences_de_l_ingénieur.object_key}/",
                **params,
            )

            assert response.status_code == 404


def test_read_subject_ok():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        insert_mocks(db, "subjects")

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get(
                f"/subjects/{mocks.subjects.mathematiques.object_key}/", **params
            )

            assert response.status_code == 200
            assert response.json() == json.loads(mocks.subjects.mathematiques.json())


def test_create_subject():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.post(
                "/subjects/",
                json={
                    "color": "red",
                    "name": "Sciences de l'ingénieur",
                    "weight": 1.0,
                    "goal": 3.67e-1,
                },
                **params,
            )

            assert response.status_code == 201
            for key, value in {
                "color": "red",
                "name": "Sciences de l'ingénieur",
                "slug": "sciences-de-l-ingenieur",
                "weight": 1.0,
                "goal": 3.67e-1,
                "location": "",
            }.items():
                assert response.json()[key] == value

            assert "_key" in response.json().keys()

            assert db.collection("subjects").all().count() == 1
            assert db.collection("subjects").get(response.json()["_key"]) is not None


def test_update_a_subject():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        insert_mocks(db, "subjects")

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.patch(
                f"/subjects/{mocks.subjects.français.object_key}",
                json={"name": "François"},
                **params,
            )

            assert response.status_code == 200
            assert response.json()["color"] == str(mocks.subjects.français.color)
            assert response.json()["name"] == "François"
            assert response.json()["slug"] == "francois"


def test_delete_subject():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        db.collection("subjects").insert(mocks.subjects.mathematiques.json())
        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.delete(
                f"/subjects/{mocks.subjects.mathematiques.object_key}", **params
            )

            assert response.status_code == status.HTTP_204_NO_CONTENT
            assert not response.text
            assert db.collection("subjects").all().count() == 0
