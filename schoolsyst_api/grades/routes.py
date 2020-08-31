from typing import List

from arango.database import StandardDatabase
from fastapi import Depends
from fastapi_utils.inferring_router import InferringRouter
from schoolsyst_api import database
from schoolsyst_api.accounts.users import User, get_current_confirmed_user
from schoolsyst_api.grades.models import Grade, InGrade, PatchGrade
from schoolsyst_api.models import ObjectBareKey
from schoolsyst_api.resource_base import ResourceRoutesGenerator

router = InferringRouter()
helper = ResourceRoutesGenerator(
    name_sg="grade", name_pl="grades", model_in=InGrade, model_out=Grade
)


@router.get("/grades/")
def list_grades(
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> List[Grade]:
    return helper.list(db, current_user)


@router.post("/grades/")
def create_grade(
    grade: InGrade,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Grade:
    return helper.create(db, current_user, grade)


@router.get("/grades/{key}")
def get_grade(
    key: ObjectBareKey,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Grade:
    return helper.get(db, current_user, key)


@router.delete("/grades/{key}")
def delete_grade(
    key: ObjectBareKey,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
):
    return helper.delete(db, current_user, key)


@router.patch("/grades/{key}")
def patch_grade(
    key: ObjectBareKey,
    changes: PatchGrade,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Grade:
    return helper.update(db, current_user, key, changes)
