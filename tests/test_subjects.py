from arango.database import StandardDatabase
from tests import ALICE_PASSWORD, authed_request, client, database_mock, mocks


def create_user(db: StandardDatabase):
    db.collection("users").insert(mocks.users.alice.json(by_alias=True))


def test_list_subjects():
    with database_mock() as db:
        db: StandardDatabase

        assert db.collection("subjects").all().count() == 0
        create_user(db)
        db.collection("subjects").insert(mocks.subjects.francais.json(by_alias=True))
        db.collection("subjects").insert(
            mocks.subjects.mathematiques.json(by_alias=True)
        )
        db.collection("subjects").insert(
            mocks.subjects.sciences_de_l_ingénieur.json(by_alias=True)
        )

        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            response = client.get("/subjects/", **params)
            keys = [s["_key"] for s in response.json()]

            assert response.status_code == 200
            assert len(response.json()) == 2
            assert mocks.subjects.sciences_de_l_ingénieur._key not in keys
            assert all(
                [
                    s._key in keys
                    for s in (mocks.subjects.francais, mocks.subjects.mathematiques)
                ]
            )
