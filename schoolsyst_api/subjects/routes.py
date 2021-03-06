from arango.database import StandardDatabase
from fastapi import Depends, status
from fastapi_utils.inferring_router import InferringRouter
from schoolsyst_api import database
from schoolsyst_api.accounts.models import User
from schoolsyst_api.accounts.users import get_current_confirmed_user
from schoolsyst_api.models import ObjectBareKey
from schoolsyst_api.resource_base import ResourceRoutesGenerator
from schoolsyst_api.subjects.models import InSubject, PatchSubject, Subject

router = InferringRouter()


helper = ResourceRoutesGenerator(
    name_sg="subject", name_pl="subjects", model_in=InSubject, model_out=Subject,
)


@router.post("/subjects/", status_code=status.HTTP_201_CREATED)
def create_subject(
    subjects: InSubject,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Subject:
    return helper.create(db, current_user, subjects)


@router.get("/subjects/")
def list_subjects(
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> list[Subject]:
    return helper.list(db, current_user)


@router.patch("/subjects/{key}")
def update_subject(
    key: ObjectBareKey,
    changes: PatchSubject,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Subject:
    return helper.update(db, current_user, key, changes)


@router.get("/subjects/{key}")
def get_subject(
    key: ObjectBareKey,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Subject:
    return helper.get(db, current_user, key)


delete_a_subject_responses = {
    204: {},
    403: {"description": "No subject with key {} found"},
    404: {"description": "Currently logged-in user does not own the specified subject"},
}


@router.delete(
    "/subjects/{key}",
    responses=delete_a_subject_responses,
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_subject(
    key: ObjectBareKey,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
):
    return helper.delete(db, current_user, key)
