from datetime import date, time

from schoolsyst_api.models import WeekType
from schoolsyst_api.schedule import current_week_type
from schoolsyst_api.schedule.models import Event
from tests.mocks import JOHN_KEY


def test_current_week_type():
    """
    Four cases:

    starting_week_type  even   odd
    current_week_is:
                  even    x     x
                  odd     x     x
    """
    assert (
        current_week_type(
            starting_week_type=WeekType.even,
            year_start=date(2020, 9, 1),
            current_date=date(2020, 9, 2),
        )
        == WeekType.even
    )
    assert (
        current_week_type(
            starting_week_type=WeekType.even,
            year_start=date(2020, 9, 1),
            current_date=date(2020, 9, 11),
        )
        == WeekType.odd
    )
    assert (
        current_week_type(
            starting_week_type=WeekType.odd,
            year_start=date(2020, 9, 1),
            current_date=date(2020, 9, 2),
        )
        == WeekType.odd
    )
    assert (
        current_week_type(
            starting_week_type=WeekType.odd,
            year_start=date(2020, 9, 1),
            current_date=date(2020, 9, 11),
        )
        == WeekType.even
    )


def test_event_on_both_weeks():
    assert not Event(
        owner_key=JOHN_KEY,
        start=time(2, 3),
        end=time(4, 5),
        day=2,
        location="lab",
        on_even_weeks=False,
        on_odd_weeks=True,
    ).on_both_weeks
    assert not Event(
        owner_key=JOHN_KEY,
        start=time(2, 3),
        end=time(4, 5),
        day=2,
        location="lab",
        on_even_weeks=True,
        on_odd_weeks=False,
    ).on_both_weeks
    assert Event(
        owner_key=JOHN_KEY,
        start=time(2, 3),
        end=time(4, 5),
        day=2,
        location="lab",
        on_even_weeks=True,
        on_odd_weeks=True,
    ).on_both_weeks
