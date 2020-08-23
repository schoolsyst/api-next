from datetime import datetime
from typing import Optional

from pydantic import PositiveFloat, confloat
from schoolsyst_api.models import OwnedResource, Primantissa


class Grade(OwnedResource):
    title: str
    actual: Optional[Primantissa] = None
    expected: Optional[Primantissa] = None
    goal: Optional[Primantissa] = None
    unit: confloat(gt=0)
    weight: PositiveFloat = 1
    obtained_at: Optional[datetime] = None
