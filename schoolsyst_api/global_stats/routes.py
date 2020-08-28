from datetime import date

from arango.database import StandardDatabase
from fastapi import Depends
from fastapi_utils.inferring_router import InferringRouter
from pydantic import PositiveInt
from schoolsyst_api import database
from schoolsyst_api.global_stats.models import HomeworkCompletedStats
from schoolsyst_api.homework.models import Homework

router = InferringRouter()


@router.get("/$/registered_users", summary="Get the number of registered users")
def get_global_stats_registered_users(
    db: StandardDatabase = Depends(database.get),
) -> PositiveInt:
    return db.collection("users").all().count()


@router.get("/$/confirmed_users", summary="Get the number of confirmed users")
def get_global_stats_confirmed_users(
    db: StandardDatabase = Depends(database.get),
) -> PositiveInt:
    """
    The number of registered users which have confirmed their email address.
    """
    return db.collection("users").find({"email_is_confirmed": True}).count()


@router.get("/$/homework_completed")
def get_global_stats_homework_completed(
    db: StandardDatabase = Depends(database.get),
) -> HomeworkCompletedStats:
    all_time = 0
    year = 0
    week = 0
    month = 0

    for doc in db.collection("homework").all():
        homework = Homework(**doc)
        all_time += 1
        if homework.updated_at.isocalendar()[1] == date.today().isocalendar()[1]:
            week += 1
            month += 1
            year += 1
        elif homework.updated_at.month == date.today().month:
            month += 1
            year += 1
        elif homework.updated_at.year == date.today().year:
            year += 1

    return HomeworkCompletedStats(all_time=all_time, year=year, week=week, month=month)
