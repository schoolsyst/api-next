import json
from datetime import datetime

from arango.database import StandardDatabase
from fastapi import status
from schoolsyst_api.settings.models import InSettings, Settings
from schoolsyst_api.settings.routes import get_default_settings
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


def test_update_settings():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        insert_mocks(db, "settings")
        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            result = client.patch("/settings", json={"grades_unit": 10}, **params)
            expected = {
                **json.loads(mocks.settings.alice.json(by_alias=True)),
                "grades_unit": 10,
            }

            assert result.status_code == 200
            assert result.json()["grades_unit"] == 10
            for key in InSettings().dict(by_alias=True).keys():
                if key in ("grades_unit", "updated_at"):
                    pass
                assert result.json()[key] == expected[key]
            updated_at = Settings(**result.json()).updated_at
            assert updated_at.date() == datetime.now().date()
            assert updated_at.hour == datetime.now().hour
            assert updated_at.minute == datetime.now().minute
            assert updated_at.second == datetime.now().second


def test_reset_all_settings():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        insert_mocks(db, "settings")
        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            result = client.delete("/settings", **params)
            assert result.status_code == 200
            for key, value in json.loads(
                get_default_settings().json(by_alias=True)
            ).items():
                assert result.json()[key] == value


def test_reset_setting():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        insert_mocks(db, "settings")
        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            result = client.delete("/settings/offdays", **params)
            expected = {
                **json.loads(mocks.settings.alice.json(by_alias=True)),
                "offdays": json.loads(get_default_settings().json())["offdays"],
            }
            assert result.status_code == 200
            assert result.json() == expected


def test_reset_setting_unknown_setting_key():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        insert_mocks(db, "settings")
        with authed_request(client, "alice", ALICE_PASSWORD) as params:
            result = client.delete("/settings/lorem_ipsum", **params)
            assert result.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            # TODO: test the validation error's body
