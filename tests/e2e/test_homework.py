import json

from arango.database import StandardDatabase
from fastapi import status
from schoolsyst_api.homework.models import HomeworkType
from tests import authed_request, client, database_mock, insert_mocks, mocks
from tests.mocks import ALICE_PASSWORD


def test_list_homework():
    with database_mock() as db:
        db: StandardDatabase

        assert db.collection("homework").all().count() == 0
        insert_mocks(db, "users")
        insert_mocks(db, "homework")

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get("/homework/", **params)

            assert response.status_code == 200
            assert len(response.json()) == 1
            assert (
                response.json()[0]["_key"]
                == mocks.homework.exos_math_not_completed_of_alice._key
            )

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get("/homework/?all=yes", **params)

            assert response.status_code == 200
            assert len(response.json()) == 2
            assert mocks.homework.test_si_john_half_completed._key not in [
                h["_key"] for h in response.json()
            ]


def test_read_homework_not_authed():
    with database_mock():
        response = client.get("/homework/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_read_homework_not_found():
    with database_mock() as db:
        db: StandardDatabase

        insert_mocks(db, "users")
        db.collection("homework").insert(
            mocks.homework.exos_math_not_completed_of_alice.json(by_alias=True)
        )

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get(
                f"/homework/{mocks.homework.coursework_français_completed_alice.object_key}/",
                **params,
            )
            assert response.status_code == 404


def test_read_homework_not_owned_by_current_user():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        db.collection("homework").insert(
            mocks.homework.test_si_john_half_completed.json()
        )

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get(
                f"/homework/{mocks.homework.test_si_john_half_completed.object_key}/",
                **params,
            )

            assert response.status_code == 404


def test_read_homework_ok():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        db.collection("homework").insert(
            mocks.homework.coursework_français_completed_alice.json()
        )

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get(
                f"/homework/{mocks.homework.coursework_français_completed_alice.object_key}/",
                **params,
            )

            assert response.status_code == 200
            assert response.json() == json.loads(
                mocks.homework.coursework_français_completed_alice.json()
            )


def test_create_homework():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        insert_mocks(db, "subjects")

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.post(
                "/homework/",
                json={
                    "subject_key": mocks.subjects.sciences_de_l_ingénieur._key,
                    "title": "Cinématique",
                    "type": HomeworkType.test,
                    "details": "Aliquip sit aute ea pariatur.",
                },
                **params,
            )

            assert response.status_code == 201
            for key, value in {
                "subject_key": mocks.subjects.sciences_de_l_ingénieur._key,
                "title": "Cinématique",
                "type": HomeworkType.test,
                "details": "Aliquip sit aute ea pariatur.",
            }.items():
                assert response.json()[key] == value

            assert "_key" in response.json().keys()

            assert db.collection("homework").all().count() == 1
            assert db.collection("homework").get(response.json()["_key"]) is not None


def test_update_a_homework():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        insert_mocks(db, "homework")

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.patch(
                f"/homework/{mocks.homework.coursework_français_completed_alice.object_key}",
                json={"progress": 0.5},
                **params,
            )

            assert response.status_code == 200
            assert response.json()["progress"] == 0.5
            assert response.json()["subject_key"] == mocks.subjects.français._key


def test_delete_homework():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        db.collection("homework").insert(
            mocks.homework.exos_math_not_completed_of_alice.json()
        )
        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.delete(
                f"/homework/{mocks.homework.exos_math_not_completed_of_alice.object_key}",
                **params,
            )

            assert response.status_code == status.HTTP_204_NO_CONTENT
            assert not response.text
            assert db.collection("homework").all().count() == 0
