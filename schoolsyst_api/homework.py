from typing import List

from arango.database import StandardDatabase
from fastapi import Depends, Query, status
from fastapi_utils.inferring_router import InferringRouter
from schoolsyst_api import database
from schoolsyst_api.accounts.users import get_current_confirmed_user
from schoolsyst_api.models import Homework, InHomework, ObjectBareKey, User
from schoolsyst_api.resource_base import ResourceRoutesGenerator

router = InferringRouter()

helper = ResourceRoutesGenerator(
    name_sg="homework", name_pl="homework", model_in=InHomework, model_out=Homework,
)


@router.post("/homework/", status_code=status.HTTP_201_CREATED)
def create_a_homework(
    homework: InHomework,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Homework:
    return helper.create(db, current_user, homework)


@router.get("/homework/")
def list_homework(
    all: bool = Query(False),
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> List[Homework]:
    """
    If ?all is not specified, do not return completed homework
    """
    homework = helper.list(db, current_user)
    if not all:
        homework = [h for h in homework if not Homework(**h).completed]
    return homework


@router.patch("/homework/{key}")
def update_a_homework(
    key: ObjectBareKey,
    changes: InHomework,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Homework:
    return helper.update(db, current_user, key, changes)


@router.get("/subjects/{key}")
def get_a_homework(
    key: ObjectBareKey,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Homework:
    return helper.get(db, current_user, key)


delete_a_homework_responses = {
    204: {},
    403: {"description": "No subject with key {} found"},
    404: {"description": "Currently logged-in user does not own the specified subject"},
}


@router.delete(
    "/homework/{key}",
    responses=delete_a_homework_responses,
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_a_subject(
    key: ObjectBareKey,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
):
    return helper.delete(db, current_user, key)
