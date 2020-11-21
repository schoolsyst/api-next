from datetime import datetime
from typing import Optional

from pydantic import PositiveFloat, confloat
from schoolsyst_api.models import BaseModel, ObjectKey, OwnedResource, Primantissa


class InGrade(BaseModel):
    """
    A grade.
    """

    title: str
    unit: confloat(gt=0)
    details: str = ""
    subject_key: Optional[ObjectKey] = None
    actual: Optional[Primantissa] = None
    expected: Optional[Primantissa] = None
    goal: Optional[Primantissa] = None
    weight: PositiveFloat = 1
    obtained_at: Optional[datetime] = None


class PatchGrade(InGrade):
    """
    Special model used to patch grades.
    """

    title: Optional[str] = None
    unit: Optional[confloat(gt=0)] = None


class Grade(InGrade, OwnedResource):
    pass
