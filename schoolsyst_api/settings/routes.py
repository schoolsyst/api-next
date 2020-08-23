import json
from datetime import datetime
from typing import Any

from arango.database import StandardDatabase
from fastapi import Depends
from fastapi_utils.inferring_router import InferringRouter
from schoolsyst_api import database, settings
from schoolsyst_api.accounts.models import User
from schoolsyst_api.accounts.users import get_current_confirmed_user
from schoolsyst_api.settings.models import InSettings, SettingKey, Settings

router = InferringRouter()


@router.get("/default_settings")
def get_default_settings() -> InSettings:
    return InSettings()


@router.get("/settings")
def read_settings(settings: Settings = Depends(settings.get)) -> Settings:
    return settings


@router.patch("/settings")
def update_some_settings(
    changes: InSettings,
    db: StandardDatabase = Depends(database.get),
    settings: Settings = Depends(settings.get),
) -> Settings:
    updated_settings = {
        **json.loads(settings.json()),
        **json.loads(changes.json(exclude_unset=True)),
        "updated_at": datetime.now().isoformat(sep="T"),
    }
    new_settings = db.collection("settings").update(updated_settings, return_new=True)[
        "new"
    ]
    return Settings(**new_settings)


@router.delete("/settings")
def reset_all_settings(
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Settings:
    # instead of deleting and re-inserting, update with a completely new object.
    settings = Settings(key=current_user.key, updated_at=datetime.now())
    db.collection("settings").update(settings.json(by_alias=True))
    return settings


@router.delete("/settings/{setting_key}")
def reset_a_setting(
    setting_key: SettingKey,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Any:
    default_settings = InSettings()
    new_settings = db.collection("settings").update(
        {
            "_key": current_user.key,
            setting_key: json.loads(default_settings.json())[setting_key],
        },
        return_new=True,
    )

    return new_settings[setting_key]