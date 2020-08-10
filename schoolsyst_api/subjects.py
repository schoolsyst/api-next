import json
from datetime import datetime
from typing import List

from arango.database import StandardDatabase
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from schoolsyst_api import database
from schoolsyst_api.accounts.users import get_current_confirmed_user
from schoolsyst_api.models import (
    OBJECT_KEY_FORMAT,
    InSubject,
    ObjectBareKey,
    Subject,
    User,
)

router = APIRouter()


@router.post("/subjects/", status_code=status.HTTP_201_CREATED)
def create_a_subject(
    subject: InSubject,
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
) -> Subject:
    # create a subject from the user's InSubject
    subject = Subject(**subject.dict(), owner_key=current_user.key)
    subject.created_at = datetime.now()
    db.collection("subjects").insert(subject.json(by_alias=True))
    return subject


@router.get("/subjects/")
def list_subjects(
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
) -> List[Subject]:
    cursor = db.collection("subjects").find({"owner_key": str(current_user.key)})
    return [batch for batch in cursor]


@router.patch("/subjects/{key}")
def update_a_subject(
    key: ObjectBareKey,
    changes: InSubject,
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
) -> Subject:
    full_key = OBJECT_KEY_FORMAT.format(owner=current_user.key, object=key)
    subject = db.collection("subjects").get(full_key)

    # Because of how the _id's are constructed, we can't stumble upon an object which
    # is not owned by the user
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No subject with key {full_key} found",
        )

    subject = Subject(**subject)
    updated_subject = {
        **json.loads(subject.json()),
        **json.loads(changes.json(exclude_unset=True)),
        "updated_at": datetime.now().isoformat(sep="T"),
    }
    return db.collection("subjects").update(updated_subject, return_new=True)["new"]


@router.get("/subjects/{key}")
def get_a_subject(
    key: ObjectBareKey,
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
) -> Subject:
    full_key = f"{current_user.key}:{key}"
    subject = db.collection("subjects").get(full_key)

    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No subject with key {full_key} found",
        )

    subject = Subject(**subject)

    if subject.owner_key != current_user.key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Currently logged-in user does not own the specified subject",
        )

    return subject


delete_a_subject_responses = {
    204: {},
    403: {"description": "No subject with key {} found"},
    404: {"description": "Currently logged-in user does not own the specified subject"},
}


@router.delete("/subjects/{key}", responses={204: {}})
def delete_a_subject(
    key: ObjectBareKey,
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
):
    full_key = f"{current_user.key}:{key}"
    subject = db.collection("subjects").get(full_key)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=delete_a_subject_responses[404]["description"].format(full_key),
        )

    subject = Subject(**subject)

    if subject.owner_key != current_user.key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=delete_a_subject_responses[403]["description"],
        )

    db.collection("subjects").delete(full_key)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
