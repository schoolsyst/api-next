import json
from datetime import datetime
from typing import Any

from arango.database import StandardDatabase
from fastapi import HTTPException, Response, status
from schoolsyst_api.accounts.models import User
from schoolsyst_api.models import OBJECT_KEY_FORMAT, ObjectBareKey


class ResourceRoutesGenerator:
    def __init__(
        self, name_sg: str, name_pl: str, model_in: Any, model_out: Any,
    ) -> None:
        self.name_pl = name_pl
        self.name_sg = name_sg
        self.model_in = model_in
        self.model_out = model_out

    def list(self, db: StandardDatabase, current_user: User):
        cursor = db.collection(self.name_pl).find({"owner_key": current_user.key})
        return [self.model_out(**item) for item in cursor]

    def get(self, db: StandardDatabase, current_user: User, key: ObjectBareKey):
        full_key = OBJECT_KEY_FORMAT.format(object=key, owner=current_user.key)
        resource = db.collection(self.name_pl).get(full_key)

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {self.name_sg} with key {full_key} found",
            )

        resource = self.model_out(**resource)

        if resource.owner_key != current_user.key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Currently logged-in user does not own the specified {self.name_sg}",
            )

        return resource

    def create(self, db: StandardDatabase, current_user: User, data):
        return self.model_out(
            **db.collection(self.name_pl).insert(
                self.model_out(**data.dict(), owner_key=current_user.key).json(
                    by_alias=True
                ),
                return_new=True,
            )["new"]
        )

    def update(
        self, db: StandardDatabase, current_user: User, key: ObjectBareKey, changes
    ):
        resource = self.get(db, current_user, key)
        updated_resource = {
            **json.loads(resource.json()),
            **json.loads(changes.json(exclude_unset=True)),
            "updated_at": datetime.now().isoformat(sep="T"),
        }
        new_resource = db.collection(self.name_pl).update(
            updated_resource, return_new=True
        )["new"]
        return self.model_out(**new_resource)

    def delete(self, db: StandardDatabase, current_user: User, key: ObjectBareKey):
        full_key = OBJECT_KEY_FORMAT.format(object=key, owner=current_user.key)
        resource = db.collection(self.name_pl).get(full_key)
        if resource is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {self.name_sg} with key {full_key} found",
            )

        resource = self.model_out(**resource)

        if resource.owner_key != current_user.key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Currently logged-in user does not own the specified subject",
            )

        db.collection(self.name_pl).delete(full_key)

        return Response(status_code=status.HTTP_204_NO_CONTENT)
