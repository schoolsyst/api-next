from arango.database import StandardDatabase
from fastapi import Depends
from schoolsyst_api import database
from schoolsyst_api.accounts.models import User
from schoolsyst_api.accounts.users import get_current_confirmed_user
from schoolsyst_api.settings.models import Settings


def get(
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Settings:
    """
    Gets the settings for the current user.
    If the settings are created when getting them (if the user has no settings tied to him),
    the return value is:

        (settings, True)

    and else:

        (settings, False)
    """
    doc = db.collection("settings").get(current_user.key)
    # If the user has no settings tied to him, create them with the default values.
    if doc is None:
        doc = db.collection("settings").insert(
            Settings(_key=current_user.key).json(by_alias=True), return_new=True
        )["new"]

    return Settings(**doc)
