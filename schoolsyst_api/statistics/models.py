from typing import Optional

from pydantic import BaseModel, PositiveFloat
from schoolsyst_api.models import Primantissa


class MeanStats(BaseModel):
    """
    Statistics for means
    """

    real: Optional[Primantissa] = None
    estimated: Optional[Primantissa] = None
    latest_grade_impact: Optional[float] = None


class GradeStats(BaseModel):
    """
    Statistics for grades, for one specific subject or for all of them
    """

    mean: MeanStats
    latest_grade_impact_on_percentage_of_goal: Optional[float] = None
    percentage_of_goal: Optional[PositiveFloat] = None
    goal: Optional[Primantissa] = None


class CountAndPercentage(BaseModel):
    """
    Re-used object containing a count and a percentage of that count over some total.
    """

    percent: Primantissa
    count: int


class HomeworkStats(BaseModel):
    """
    Statistics for homework
    """

    completed: CountAndPercentage
    late: CountAndPercentage
