from typing import List

from schoolsyst_api.accounts.models import User
from schoolsyst_api.grades.models import Grade
from schoolsyst_api.homework.models import Homework
from schoolsyst_api.learn.models import Quiz
from schoolsyst_api.models import BaseModel
from schoolsyst_api.notes.models import Note
from schoolsyst_api.schedule.models import Event, EventMutation
from schoolsyst_api.settings.models import Settings
from schoolsyst_api.subjects.models import Subject


class PersonalArchive(BaseModel):
    subjects: List[Subject]
    users: List[User]
    settings: List[Settings]
    quizzes: List[Quiz]
    notes: List[Note]
    grades: List[Grade]
    homework: List[Homework]
    events: List[Event]
    event_mutations: List[EventMutation]
