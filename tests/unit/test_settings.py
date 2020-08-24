import schoolsyst_api.settings
from arango.database import StandardDatabase
from schoolsyst_api.settings.models import InSettings
from tests import database_mock, insert_mocks, mocks


def test_get():
    with database_mock() as db:
        db: StandardDatabase
        insert_mocks(db, "users")
        default_settings = InSettings()
        # for now users have no tied settings
        result = schoolsyst_api.settings.get(db, mocks.users.john)
        for prop in default_settings.dict(by_alias=True).keys():
            assert getattr(result, prop) == getattr(default_settings, prop)

        # test that the user now has a settings object tied to him in the db
        assert db.collection("settings").get(mocks.users.john.key) is not None
