from datetime import datetime
from enum import auto
from typing import List, Optional

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
    progress: Primantissa = 0
    tasks: List[Task] = []
    notes: List[ObjectKey] = []
    grades: List[ObjectKey] = []

    @property
    def completed(self) -> bool:
        return self.progress >= 1

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
        This is decoupled from `self.progress` as the progress can be set manually.

        TODO: Make `progress` read-only, and add an endpoint to complete a homework, which will:
        - if the homework has any tasks:
            mark all of the homework's tasks as completed
        - else:
            set `progress` to 1
        """
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
