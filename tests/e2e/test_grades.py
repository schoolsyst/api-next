import json
from datetime import datetime

from arango.database import StandardDatabase
from fastapi import status
from tests import authed_request, client, database_mock, insert_mocks, mocks
from tests.mocks import ALICE_PASSWORD


def test_list_grades():
    with database_mock() as db:
        db: StandardDatabase

        assert db.collection("grades").all().count() == 0
        insert_mocks(db, "users")
        insert_mocks(db, "grades")

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get("/grades/", **params)

            assert response.status_code == 200
            assert len(response.json()) == 3
            assert mocks.grades.john_nosubject._key not in [
                v["_key"] for v in response.json()
            ]


def test_read_grades_not_authed():
    with database_mock():
        response = client.get("/grades/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_read_grades_not_found():
    with database_mock() as db:
        db: StandardDatabase

        insert_mocks(db, "users")
        db.collection("grades").insert(mocks.grades.alice_nietzsche.json(by_alias=True))

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get(
                f"/grades/{mocks.grades.alice_trigo.object_key}", **params,
            )
            assert response.status_code == 404


def test_read_grades_not_owned_by_current_user():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        db.collection("grades").insert(mocks.grades.john_nosubject.json())

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get(
                f"/grades/{mocks.grades.john_nosubject.object_key}/", **params,
            )

            assert response.status_code == 404


def test_read_grades_ok():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        db.collection("grades").insert(mocks.grades.alice_trigo.json())

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get(
                f"/grades/{mocks.grades.alice_trigo.object_key}/", **params,
            )

            assert response.status_code == 200
            assert response.json() == json.loads(mocks.grades.alice_trigo.json())


def test_create_grades():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        insert_mocks(db, "grades")

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.post(
                "/grades/",
                json={
                    "subject_key": mocks.subjects.sciences_de_l_ingénieur._key,
                    "title": "Cinématique",
                    "unit": 95,
                    "details": "Aliquip sit aute ea pariatur.",
                },
                **params,
            )

            assert response.status_code == 201
            for key, value in {
                "subject_key": mocks.subjects.sciences_de_l_ingénieur._key,
                "title": "Cinématique",
                "unit": 95,
                "details": "Aliquip sit aute ea pariatur.",
            }.items():
                assert response.json()[key] == value

            assert "_key" in response.json().keys()

            assert db.collection("grades").all().count() == 5
            assert db.collection("grades").get(response.json()["_key"]) is not None


def test_update_grade():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        insert_mocks(db, "grades")

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.patch(
                f"/grades/{mocks.grades.alice_unobtained.object_key}",
                json={"actual": 0.5},
                **params,
            )

            assert response.status_code == 200
            assert response.json()["actual"] == 0.5
            assert response.json()["subject_key"] == mocks.subjects.français._key
            obtained_at = datetime.fromisoformat(response.json()["obtained_at"])
            assert abs(datetime.now().timestamp() - obtained_at.timestamp()) < 1


def test_delete_grades():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        insert_mocks(db, "grades")
        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.delete(
                f"/grades/{mocks.grades.alice_trigo.object_key}", **params,
            )

            assert response.status_code == status.HTTP_204_NO_CONTENT
            assert not response.text
            assert db.collection("grades").all().count() == 3
            assert db.collection("grades").get(mocks.grades.alice_trigo._key) is None
