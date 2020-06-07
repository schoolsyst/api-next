from arango.database import StandardDatabase
from schoolsyst_api.accounts import get_user
from tests import database_mock, mocks


def test_get_user():
    with database_mock() as db:
        db: StandardDatabase
        db.collection("users").insert(mocks.users.john.json(by_alias=True))
        assert get_user(db, mocks.users.john.username) == mocks.users.john
        assert get_user(db, "hmmmmmm") is None
