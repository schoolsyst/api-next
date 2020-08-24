from datetime import date, datetime

from schoolsyst_api.accounts.auth import hash_password
from schoolsyst_api.accounts.models import DBUser
from schoolsyst_api.homework.models import Homework, HomeworkType
from schoolsyst_api.models import DateRange, WeekType
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


class homework:
    exos_math_not_completed_of_alice = Homework(
        owner_key=ALICE_KEY,
        subject_key=subjects.mathematiques._key,
        title="Ex. 4, 5, 5 p. 89",
        type=HomeworkType.exercise,
        details="Lorem ipsum dolor sit amet",
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
