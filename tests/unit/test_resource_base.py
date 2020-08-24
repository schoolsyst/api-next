from datetime import datetime
from typing import Optional

import fastapi.exceptions
from arango.database import StandardDatabase
from parse import parse
from pytest import raises
from schoolsyst_api.models import (
    OBJECT_KEY_FORMAT,
    BaseModel,
    OwnedResource,
    objectbarekey,
)
from schoolsyst_api.resource_base import ResourceRoutesGenerator
from tests import database_mock, insert_mocks, mocks


class Lorem(BaseModel):
    dolor: int
    sit: str


class LoremPatch(BaseModel):
    dolor: Optional[int] = None
    sit: Optional[str] = None


class LoremOut(Lorem, OwnedResource):
    pass


loremeggs = LoremOut(dolor=47, sit="spam", owner_key=mocks.users.alice.key)
lorembacon = LoremOut(dolor=47, sit="eggs", owner_key=mocks.users.john.key)


def setup_helper_and_db(db) -> ResourceRoutesGenerator:
    db.create_collection("ipsum")
    db.collection("ipsum").insert(loremeggs.json(by_alias=True))
    db.collection("ipsum").insert(lorembacon.json(by_alias=True))
    insert_mocks(db, "users")
    return ResourceRoutesGenerator("lorem", "ipsum", Lorem, LoremOut)


def test_list_ok():
    with database_mock() as db:
        helper = setup_helper_and_db(db)
        result = helper.list(db, mocks.users.john)
        assert len(result) == 1
        assert result[0] == lorembacon


def test_get_not_found():
    with database_mock() as db:
        db: StandardDatabase
        helper = setup_helper_and_db(db)
        try_with_key = objectbarekey()
        with raises(fastapi.exceptions.HTTPException) as error:
            helper.get(db, mocks.users.john, try_with_key)

        assert error.value.status_code == 404
        assert (
            error.value.detail
            == f"No lorem with key {OBJECT_KEY_FORMAT.format(owner=mocks.users.john.key, object=try_with_key)} found"
        )


def test_get_not_owned():
    with database_mock() as db:
        db: StandardDatabase
        helper = setup_helper_and_db(db)
        try_with_key = loremeggs.object_key
        with raises(fastapi.exceptions.HTTPException) as error:
            helper.get(db, mocks.users.john, try_with_key)

        assert error.value.status_code == 404
        assert (
            error.value.detail
            == f"No lorem with key {OBJECT_KEY_FORMAT.format(owner=mocks.users.john.key, object=try_with_key)} found"
        )


def test_get_ok():
    with database_mock() as db:
        db: StandardDatabase
        helper = setup_helper_and_db(db)
        assert helper.get(db, mocks.users.john, lorembacon.object_key) == lorembacon


def test_create_ok():
    with database_mock() as db:
        db: StandardDatabase
        helper = setup_helper_and_db(db)
        result = helper.create(
            db, mocks.users.john, Lorem(dolor=lorembacon.dolor, sit=lorembacon.sit)
        ).dict(by_alias=True)
        result_creation_date: datetime = result["created_at"]

        for key, value in {
            "dolor": lorembacon.dolor,
            "sit": lorembacon.sit,
            "owner_key": lorembacon.owner_key,
        }.items():
            assert result[key] == value

        assert result_creation_date.date() == datetime.now().date()
        assert result_creation_date.hour == datetime.now().hour
        assert result_creation_date.minute == datetime.now().minute
        parsed_full_key = parse(OBJECT_KEY_FORMAT, result["_key"])
        assert parsed_full_key.named["owner"] == lorembacon.owner_key
        assert parsed_full_key.named["object"] == result["object_key"]


def test_update_ok():
    with database_mock() as db:
        db: StandardDatabase
        helper = setup_helper_and_db(db)
        loremham = LoremOut(**{**lorembacon.dict(by_alias=True), "dolor": 88})
        result = helper.update(
            db,
            mocks.users.john,
            lorembacon.object_key,
            LoremPatch(dolor=loremham.dolor),
        ).dict(by_alias=True)
        result_update_date = result["updated_at"]
        for key, value in {
            "dolor": loremham.dolor,
            "sit": loremham.sit,
            "owner_key": loremham.owner_key,
        }.items():
            assert result[key] == value

        assert result_update_date.date() == datetime.now().date()
        assert result_update_date.hour == datetime.now().hour
        assert result_update_date.minute == datetime.now().minute
        parsed_full_key = parse(OBJECT_KEY_FORMAT, result["_key"])
        assert parsed_full_key.named["owner"] == lorembacon.owner_key
        assert parsed_full_key.named["object"] == result["object_key"]


def test_update_not_found():
    with database_mock() as db:
        db: StandardDatabase
        helper = setup_helper_and_db(db)
        loremham = LoremOut(**{**lorembacon.dict(by_alias=True), "dolor": 88})
        try_with_key = objectbarekey()

        with raises(fastapi.exceptions.HTTPException) as error:
            helper.update(
                db, mocks.users.john, try_with_key, LoremPatch(dolor=loremham.dolor),
            )

        assert error.value.status_code == 404
        assert (
            error.value.detail
            == f"No lorem with key {OBJECT_KEY_FORMAT.format(owner=mocks.users.john.key, object=try_with_key)} found"
        )
        assert db.collection("ipsum").get(try_with_key) is None


def test_update_not_owned():
    with database_mock() as db:
        db: StandardDatabase
        helper = setup_helper_and_db(db)
        loremham = LoremOut(**{**lorembacon.dict(by_alias=True), "dolor": 88})
        try_with_key = loremeggs.object_key

        with raises(fastapi.exceptions.HTTPException) as error:
            helper.update(
                db, mocks.users.john, try_with_key, LoremPatch(dolor=loremham.dolor),
            )

        assert error.value.status_code == 404
        assert (
            error.value.detail
            == f"No lorem with key {OBJECT_KEY_FORMAT.format(owner=mocks.users.john.key, object=try_with_key)} found"
        )
        assert db.collection("ipsum").get(try_with_key) is None


def test_delete_ok():
    with database_mock() as db:
        db: StandardDatabase
        helper = setup_helper_and_db(db)
        collection_length_before_deletion = db.collection("ipsum").all().count()
        assert (
            helper.delete(db, mocks.users.john, lorembacon.object_key).status_code
            == 204
        )
        assert (
            db.collection("ipsum").all().count()
            == collection_length_before_deletion - 1
        )
        assert db.collection("ipsum").get(lorembacon._key) is None


def test_delete_not_found():
    with database_mock() as db:
        db: StandardDatabase
        helper = setup_helper_and_db(db)
        collection_length_before_deletion = db.collection("ipsum").all().count()
        try_with_key = objectbarekey()
        with raises(fastapi.exceptions.HTTPException) as error:
            helper.delete(db, mocks.users.john, try_with_key)

        assert error.value.status_code == 404
        assert (
            error.value.detail
            == f"No lorem with key {OBJECT_KEY_FORMAT.format(owner=mocks.users.john.key, object=try_with_key)} found"
        )
        assert db.collection("ipsum").all().count() == collection_length_before_deletion
        assert db.collection("ipsum").get(try_with_key) is None


def test_delete_not_owned():
    with database_mock() as db:
        db: StandardDatabase
        helper = setup_helper_and_db(db)
        collection_length_before_deletion = db.collection("ipsum").all().count()
        object_before_deletion = db.collection("ipsum").get(loremeggs._key)
        with raises(fastapi.exceptions.HTTPException) as error:
            helper.delete(db, mocks.users.john, loremeggs.object_key)

        assert error.value.status_code == 404
        assert (
            error.value.detail
            == f"No lorem with key {OBJECT_KEY_FORMAT.format(owner=mocks.users.john.key, object=loremeggs.object_key)} found"
        )
        assert db.collection("ipsum").all().count() == collection_length_before_deletion
        assert db.collection("ipsum").get(loremeggs._key) == object_before_deletion
