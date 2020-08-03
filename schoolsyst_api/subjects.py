from datetime import datetime
from typing import *

from arango.database import StandardDatabase
from arango.exceptions import DocumentGetError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
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
    subject = Subject(**subject.dict(), owner_id=current_user.key)
    subject.created_at = datetime.now()
    db.collection("subjects").insert(subject.json(by_alias=True))
    return subject


@router.get("/subjects/")
def list_subjects(
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
) -> List[Subject]:
    print(f"finding subjects with owner_id=={current_user.key}")
    cursor = db.collection("subjects").find({"owner_id": str(current_user.key)})
    return [batch for batch in cursor]


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

    if subject.owner_id != current_user.key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Currently logged-in user does not own the specified subject",
        )

    return subject


delete_a_subject_responses = {
    204: {},
    403: {"description": "No subject with UUID {} found"},
    404: {"description": "Currently logged-in user does not own the specified subject"},
}


@router.delete("/subjects/{uuid}", responses={204: {}})
def delete_a_subject(
    uuid: UUID4,
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
):
    subject = db.collection("subjects").get(str(uuid))
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=delete_a_subject_responses[404]["description"].format(uuid),
        )

    subject = Subject(**subject)

    if subject.owner_id != current_user.key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=delete_a_subject_responses[403]["description"],
        )

    db.collection("subjects").delete(str(uuid))

    return Response(status_code=status.HTTP_204_NO_CONTENT)
