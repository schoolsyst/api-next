from arango.database import StandardDatabase
from fastapi import Depends, status
from fastapi.responses import Response
from schoolsyst_api import database
from schoolsyst_api.accounts.models import User
from schoolsyst_api.accounts.users import get_current_confirmed_user
from schoolsyst_api.settings.models import Settings


def get(
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Settings:
    doc = db.collection("settings").get(current_user.key)
    # If the user has no settings tied to him, create them with the default values.
    if doc is None:
        db.collection("settings").insert(
            Settings(key=current_user.key).json(by_alias=True)
        )
        return Response(Settings(**doc), status_code=status.HTTP_201_CREATED)
    return Settings(**doc)
