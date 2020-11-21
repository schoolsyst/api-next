from datetime import datetime
from enum import auto
from typing import Optional

from fastapi_utils.enums import StrEnum
from pydantic import Field
from schoolsyst_api.models import (
    BaseModel,
    ObjectBareKey,
    ObjectKey,
    OwnedResource,
    Primantissa,
    objectbarekey,
)


class HomeworkType(StrEnum):
    """
    A type of homework. More may be added to meet everyone's use cases, but the following
    defines why I started with four types:

    criteria                        | test | coursework | to_bring | exercise
    --------------------------------|------|------------|----------|-----------
    Results in a grade              |   √  |     √      |    X     |    X
    Needs to be brought in class    |   X  |     √      |    √     |    X
    """

    test = auto()
    coursework = auto()
    to_bring = auto()
    exercise = auto()


class Task(BaseModel):
    """
    A task. Homework can have "sub" tasks (here simply called tasks).
    This helps have a stronger sense of progression on long and/or complicated homework
    (as the `progress` value can be incremented granually)
    and give students a sense of pride and accomplishment when they finally
    finish studying for that test tomorrow.

    Might add a way to make infinitely-deeply-nested task trees
    """

    key: ObjectBareKey = Field(default_factory=objectbarekey)
    title: str
    completed: bool = False
    completed_at: Optional[datetime] = None


class InHomework(BaseModel):
    title: str
    subject_key: ObjectKey
    type: HomeworkType
    details: str = ""
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    explicit_progress: Optional[Primantissa] = None
    tasks: list[Task] = []
    notes: list[ObjectKey] = []
    grades: list[ObjectKey] = []

    @property
    def completed(self) -> bool:
        return self.progress >= 1

    @property
    def progress(self) -> Primantissa:
        """
        Progress, used as the source of truth for `.completed`.
        Is either explicit_progress, if set, or progress_from_tasks.
        """
        return self.explicit_progress or self.progress_from_tasks

    @property
    def late(self) -> bool:
        return (
            not self.completed
            and self.due_at is not None
            and self.due_at < datetime.now()
        )

    @property
    def progress_from_tasks(self) -> Primantissa:
        """
        Progress as dictated by the tasks' completion.
        """
        if not len(self.tasks):
            return 0
        return len([t for t in self.tasks if t.completed]) / len(self.tasks)


class PatchHomework(InHomework):
    """
    Special model for patching a homework object.
    """

    title: Optional[str] = None
    subject_key: Optional[ObjectKey] = None
    type: Optional[HomeworkType] = None


class Homework(InHomework, OwnedResource):
    pass
