import json

from arango.database import StandardDatabase
from schoolsyst_api.settings.models import InSettings
from tests import authed_request, client, database_mock, insert_mocks, mocks
from tests.mocks import ALICE_PASSWORD


def test_get_default_settings():
    with database_mock():
        result = client.get("/default_settings").json()
        assert result == json.loads(InSettings().json(by_alias=True))


def test_get_settings():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        insert_mocks(db, "settings")
        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            result = client.get("/settings", **params).json()
            assert result == json.loads(mocks.settings.alice.json(by_alias=True))
