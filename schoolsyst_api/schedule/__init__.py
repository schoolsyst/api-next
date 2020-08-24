from datetime import date

from schoolsyst_api.models import WeekType
from schoolsyst_api.utils import daterange


def current_week_type(
    starting_week_type: WeekType, year_start: date, current_date: date
) -> WeekType:
    is_initial_weektype = False
    weeks_since_year_start = len(list(daterange(year_start, current_date, "weeks")))
    for i in range(weeks_since_year_start):
        is_initial_weektype = i % 2 == 0

    if is_initial_weektype:
        return starting_week_type
    return WeekType.even if starting_week_type == WeekType.odd else WeekType.odd
