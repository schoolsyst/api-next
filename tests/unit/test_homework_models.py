from datetime import datetime, timedelta

from schoolsyst_api.homework.models import HomeworkType, InHomework, Task
from schoolsyst_api.models import objectbarekey

hw_props = dict(title="Test", subject_key=objectbarekey(), type=HomeworkType.test)
tasks = [
    Task(title="Lorem"),
    Task(title="Ipsum"),
    Task(title="Dolor", completed=True),
    Task(title="Sit", completed=True),
    Task(title="Amet", completed=True),
]


def test_homework_completed():
    assert not InHomework(**hw_props, explicit_progress=0).completed
    assert InHomework(**hw_props, explicit_progress=1).completed
    assert not InHomework(**hw_props, explicit_progress=0.9999).completed


def test_homework_late():
    assert not InHomework(**hw_props, explicit_progress=1)
    assert InHomework(
        **hw_props,
        explicit_progress=0.4,
        due_at=(datetime.now() - timedelta(24, 20, 10))
    ).late
    assert not InHomework(
        **hw_props,
        explicit_progress=0.4,
        due_at=(datetime.now() + timedelta(24, 20, 10))
    ).late
    assert not InHomework(**hw_props, explicit_progress=0.9999, due_at=None).late


def test_homework_progress_from_tasks():
    assert InHomework(**hw_props, tasks=tasks).progress_from_tasks == 3 / 5
    assert (
        InHomework(**hw_props, tasks=tasks, explicit_progress=0.8).progress_from_tasks
        != 0.8
    )
    assert InHomework(**hw_props, tasks=[]).progress_from_tasks == 0


def test_homework_progress():
    assert InHomework(**hw_props, tasks=tasks).progress == 3 / 5
    assert InHomework(**hw_props, tasks=tasks, explicit_progress=0.8).progress == 0.8
    assert InHomework(**hw_props, tasks=[]).progress == 0
    assert InHomework(**hw_props, tasks=[], explicit_progress=0.7).progress == 0.7
