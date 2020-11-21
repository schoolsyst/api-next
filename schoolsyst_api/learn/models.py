from pydantic import PositiveInt
from schoolsyst_api.models import OwnedResource


class Quiz(OwnedResource):
    """
    A quiz object
    """

    name: str
    # questions: List[Question] = []
    # Number of trials in test mode
    tries_test: PositiveInt = 0
    # Number of trials in train mode
    tries_train: PositiveInt = 0
    # Total number of trials
    tries_total: PositiveInt = 0
    # (in seconds) the total time spent on this quizz
    time_spent: PositiveInt = 0
    # sessions: List[QuizSession] = []
