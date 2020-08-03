from datetime import datetime
from typing import *

from arango.database import StandardDatabase
from arango.exceptions import DocumentGetError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from schoolsyst_api import database
from schoolsyst_api.models import InSubject, ObjectBareKey, Subject, User
from schoolsyst_api.users import get_current_confirmed_user

router = APIRouter()


@router.post("/subjects/")
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
    print(f"finding subjects with owner_key=={current_user.key}")
    cursor = db.collection("subjects").find({"owner_key": str(current_user.key)})
    return [batch for batch in cursor]


@router.put("/subjects/{key}")
def update_a_subject(
    key: ObjectBareKey,
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
) -> Subject:
    try:
        subject = db.collection("subjects").get(f"{current_user.key}/{key}")
    except DocumentGetError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No subject with key {current_user.key}/{key} found",
        )

    subject = Subject(**subject)

    if subject.owner_key != current_user.key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Currently logged-in user does not own the specified subject",
        )

    return db.collection("subjects").update(f"{current_user.key}/{key}", subject.json())


@router.get("/subjects/{key}")
def get_a_subject(
    key: ObjectBareKey,
    current_user: User = Depends(get_current_confirmed_user),
    db: StandardDatabase = Depends(database.get),
) -> Subject:
    full_key = f"{current_user.key}/{key}"
    try:
        subject = db.get(full_key)
    except DocumentGetError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No subject with key {full_key} found",
        )

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
    full_key = f"{current_user.key}/{key}"
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
