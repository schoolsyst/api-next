from datetime import datetime
from enum import auto
from typing import List, Optional

from fastapi_utils.enums import StrEnum
from schoolsyst_api.models import BaseModel, ObjectKey, OwnedResource, Primantissa


class HomeworkType(StrEnum):
    test = auto()
    coursework = auto()
    to_bring = auto()
    exercise = auto()


class InHomework(BaseModel):
    title: str
    subject_key: ObjectKey
    type: HomeworkType
    details: str = ""
    completed_at: Optional[datetime] = None
    progress: Primantissa = 0
    notes: List[ObjectKey] = []
    grades: List[ObjectKey] = []

    @property
    def completed(self) -> bool:
        return self.progress >= 1


class PatchHomework(InHomework):
    title: Optional[str] = None
    subject_key: Optional[ObjectKey] = None
    type: Optional[HomeworkType] = None


class Homework(InHomework, OwnedResource):
    pass
