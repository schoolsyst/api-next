from datetime import date
from typing import Optional, Union

from arango.database import StandardDatabase
from fastapi import Depends
from fastapi_utils.inferring_router import InferringRouter
from schoolsyst_api import database, settings
from schoolsyst_api.accounts.models import User
from schoolsyst_api.accounts.users import get_current_confirmed_user
from schoolsyst_api.grades.models import Grade
from schoolsyst_api.models import DateRange, ObjectBareKey, Primantissa
from schoolsyst_api.settings.models import Settings
from schoolsyst_api.statistics.models import GradeStats

router = InferringRouter()


# custom ranges, trimesters, week
# - per subjec, all subjects
#     - average
#         - real
#         - estimated
#         - impact of latest grade
#     - % of goal
#         - impact of latest grade


def mean(*values: Union[int, float]) -> float:
    return sum(values) / len(values)


def weighted_mean(*values: tuple[float, float]) -> float:
    """
    Weighted average: takes tuples of (value, weight)
    and returns the average of those
    """
    return sum([value * weight for value, weight in values]) / sum(
        [weight for _, weight in values]
    )


def weighted_mean_grades(grades: list[Grade], value_attr: str) -> Primantissa:
    """
    Calculates a weighted mean of `grades` by using `getattr(grade, value_attr)`
    as the value and grade.weight as the weight
    """
    if not grades:
        return 0
    return weighted_mean(*[(getattr(g, value_attr), g.weight) for g in grades])


def percentage_of_goal(avg: Primantissa, goal: Primantissa) -> float:
    return (goal - avg) / goal


@router.get("/statistics/grades/{start}/{end}")
def get_grade_statistics(
    start: date,
    end: date,
    subject: Optional[ObjectBareKey] = None,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
    settings: Settings = Depends(settings.get),
) -> GradeStats:
    # TODO: use AQLs instead
    criterias = {"owner_key": current_user.key}
    if subject:
        criterias["subject_key"] = subject
    grades = [Grade(**g) for g in db.collection("grades").find(criterias)]
    grades = [g for g in grades if g.obtained_at in DateRange(start, end)]
    grades = sorted(grades, key=lambda g: g.obtained_at)
    ...
