from datetime import date, datetime

from schoolsyst_api.accounts.auth import hash_password
from schoolsyst_api.accounts.models import DBUser
from schoolsyst_api.grades.models import Grade
from schoolsyst_api.homework.models import Homework, HomeworkType, Task
from schoolsyst_api.models import DateRange, WeekType, objectbarekey
from schoolsyst_api.settings.models import Settings, ThemeName
from schoolsyst_api.subjects.models import Subject

ALICE_PASSWORD = "fast-unicorn-snails-dragon5"
ALICE_KEY = "8FPuamSTXK"
JOHN_PASSWORD = "dice-wears-hats9-star-game"
JOHN_KEY = "zMSLrwGwZA"


class users:
    alice = DBUser(
        _key=ALICE_KEY,
        username="alice",
        password_hash=hash_password(ALICE_PASSWORD),
        joined_at=datetime(2020, 7, 23, 22, 41, 0),
        email_is_confirmed=True,
        email="hey@alice.example.com",
    )

    john = DBUser(
        _key=JOHN_KEY,
        username="john",
        password_hash=hash_password(JOHN_PASSWORD),
        joined_at=datetime(2019, 6, 12, 12, 0, 51),
        email="john@example.com",
    )


class subjects:
    français = Subject(
        owner_key=ALICE_KEY,
        color="red",
        goal=1.0,
        room="L204",
        weight=3.0,
        name="Français",
    )

    mathematiques = Subject(
        owner_key=ALICE_KEY,
        color="cyan",
        goal=0.4,
        room="L624",
        weight=6,
        name="Mathématiques",
    )

    sciences_de_l_ingénieur = Subject(
        owner_key=JOHN_KEY,
        color="#c0ffee",
        goal=0.8,
        room="",
        weight=48,
        name="Sciences de l'ingénieur",
    )


LOWEM_DOLEM_TASK_KEY = objectbarekey()


class homework:
    exos_math_not_completed_of_alice = Homework(
        owner_key=ALICE_KEY,
        subject_key=subjects.mathematiques._key,
        title="Ex. 4, 5, 5 p. 89",
        type=HomeworkType.exercise,
        details="Lorem ipsum dolor sit amet",
        tasks=[
            Task(title="Ipsum dolor sit lorem"),
            Task(title="Lorem dolem ispa"),
            Task(title="Lowem dolem ssssap", key=LOWEM_DOLEM_TASK_KEY),
        ],
        due_at=datetime(2020, 10, 11),
    )

    coursework_français_completed_alice = Homework(
        owner_key=ALICE_KEY,
        subject_key=subjects.français._key,
        title="67 @198",
        type=HomeworkType.coursework,
        details="Labore commodo veniam nostrud elit "
        "occaecat cupidatat id labore culpa ex aute magna tempor adipisicing.",
        progress=1,
        completed_at=datetime(2020, 7, 22, 14, 57, 34),
        due_at=datetime(2020, 9, 3),
    )

    test_si_john_half_completed = Homework(
        owner_key=JOHN_KEY,
        subject_key=subjects.sciences_de_l_ingénieur._key,
        title="Cinématique",
        type=HomeworkType.test,
        details="Aliquip sit aute ea pariatur.",
    )


class settings:
    alice = Settings(
        _key=users.alice.key,
        theme=ThemeName.dark,
        year_layout=[
            DateRange(start=date(2020, 9, 1), end=date(2020, 2, 24)),
            DateRange(start=date(2021, 4, 20), end=date(2021, 5, 9)),
            DateRange(start=date(2021, 6, 2), end=date(2021, 7, 6)),
        ],
        starting_week_type=WeekType.even,
        grades_unit=20,
        offdays=[
            DateRange(start=date(2020, 10, 21), end=date(2020, 11, 4)),
            DateRange(start=date(2020, 12, 23), end=date(2020, 1, 6)),
            DateRange(start=date(2021, 2, 10), end=date(2021, 2, 24)),
            DateRange(start=date(2021, 4, 6), end=date(2021, 4, 20)),
            DateRange(start=date(2021, 5, 1), end=date(2021, 5, 2)),
            DateRange(start=date(2021, 5, 8), end=date(2021, 5, 9)),
            DateRange(start=date(2021, 5, 21), end=date(2021, 5, 25)),
            DateRange(start=date(2021, 6, 1), end=date(2021, 6, 2)),
        ],
    )

    john = Settings(
        _key=users.john.key,
        theme=ThemeName.light,
        year_layout=[
            DateRange(start=date(2020, 9, 2), end=date(2020, 2, 24)),
            DateRange(start=date(2021, 4, 20), end=date(2021, 5, 9)),
            DateRange(start=date(2021, 6, 2), end=date(2021, 7, 14)),
        ],
        starting_week_type=WeekType.odd,
        grades_unit=100,
        offdays=[
            DateRange(start=date(2020, 10, 21), end=date(2020, 11, 4)),
            DateRange(start=date(2020, 12, 23), end=date(2020, 1, 6)),
            DateRange(start=date(2021, 2, 10), end=date(2021, 2, 24)),
            DateRange(start=date(2021, 4, 6), end=date(2021, 4, 20)),
            DateRange(start=date(2021, 5, 1), end=date(2021, 5, 2)),
            DateRange(start=date(2021, 5, 8), end=date(2021, 5, 9)),
        ],
    )


class grades:
    alice_trigo = Grade(
        owner_key=ALICE_KEY,
        title="Esse qui laboris et et dolore esse non ullamco sint quis.",
        unit=20,
        subject_key=subjects.mathematiques._key,
        actual=0.86,
        expected=0.64,
        goal=0.56,
        weight=1,
        obtained_at=datetime(2020, 11, 12, 10, 31, 24),
    )

    alice_nietzsche = Grade(
        owner_key=ALICE_KEY,
        title="Anim in pariatur ut pariatur est occaecat laboris consequat.",
        unit=10,
        subject_key=subjects.français._key,
        actual=0.97,
        expected=None,
        goal=None,
        weight=3,
        obtained_at=datetime(2020, 11, 15, 16, 2, 2),
    )

    john_nosubject = Grade(
        owner_key=JOHN_KEY,
        title="Incididunt elit sunt proident id quis officia fugiat ex nulla voluptate pariatur pariatur enim.",
        unit=5,
        subject_key=None,
        actual=None,
        expected=0.49,
        goal=0.40,
        weight=0.5,
        obtained_at=None,
    )
