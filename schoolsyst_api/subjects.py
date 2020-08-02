from datetime import datetime
from typing import *

from arango.database import StandardDatabase
from arango.exceptions import DocumentGetError
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4
from schoolsyst_api import database
from schoolsyst_api.models import InSubject, Subject, User
from schoolsyst_api.users import get_current_confirmed_user

router = APIRouter()


@router.post("/subjects/")
def create_a_subject(
    subject: InSubject,
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
) -> Subject:
    # create a subject from the user's InSubject
    subject = Subject(**subject)
    subject.owner_id = current_user.uuid
    subject.created_at = datetime.now()
    db.collection("users").insert(subject.json(by_alias=True))
    return subject


@router.get("/subjects/")
def list_subjects(
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
) -> List[Subject]:
    return db.collection("subjects").find({"owner_id": current_user.key})


@router.put("/subjects/{uuid}")
def update_a_subject(
    uuid: UUID4,
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
) -> Subject:
    try:
        subject = db.collection("users").get(uuid)
    except DocumentGetError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No subject with UUID {uuid} found",
        )

    subject = Subject(**subject)

    if subject.owner_id != current_user.uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Currently logged-in user does not own the specified subject",
        )

    return db.collection("users").update(uuid, subject.json())


@router.get("/subjects/{uuid}")
def get_a_subject(
    uuid: UUID4,
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
) -> Subject:
    try:
        subject = db.get(uuid)
    except DocumentGetError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No subject with UUID {uuid} found",
        )

    if subject.owner_id != current_user.uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Currently logged-in user does not own the specified subject",
        )

    return subject


@router.delete("/subjects/{uuid}")
def delete_a_subject(
    uuid: UUID4,
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
):
    try:
        subject = db.get(uuid)
    except DocumentGetError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No subject with UUID {uuid} found",
        )

    if subject.owner_id != current_user.uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Currently logged-in user does not own the specified subject",
        )

    db.collection("subjects").delete(uuid)
