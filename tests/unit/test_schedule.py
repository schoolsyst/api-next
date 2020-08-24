from datetime import date

from schoolsyst_api.models import WeekType
from schoolsyst_api.schedule import current_week_type


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
