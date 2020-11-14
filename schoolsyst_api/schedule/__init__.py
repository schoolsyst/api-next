from datetime import date

from schoolsyst_api.models import WeekType
from schoolsyst_api.utils import daterange


def current_week_type(
    starting_week_type: WeekType, year_start: date, current_date: date
) -> WeekType:
    """
    Returns the current date's week type
    """
    # The number of weeks since the year started
    # Also the number of times the week type switched since the year started
    weeks_since_year_start = len(list(daterange(year_start, current_date, "weeks")))
    # since the week types switches every second week,
    # if the number of weeks elapsed since the beginning of the (school's) year
    # is an even number, then the current week type is the same as the one the (school's)
    # year started with.
    #
    # e.g.: the year started four weeks ago, and the first week was WeekType.even¹
    # then the current week's type is WeekType.odd, because we switched weektypes 3 times
    # and 3 is odd, so we use not the first week's WeekType but the other one.
    #
    #                week no. |  1st  |  2nd  |  3rd  | 4th (current) |  5th  | ...
    # weeks_since_year_start  |   0   |   1   |   2   |        3      |   4   | ...
    #       parity of ↑       | even  |  odd  |  even |      odd      |  even | ...
    # returned WeekType       | even  |  odd  |  even |      odd      |  even | ...
    #                             ↑
    #                     starting_week_type
    #
    # You can also think of weeks_since_year_start as the number of weektype switches
    # that have occurred since the start of the year.
    #
    # ¹Do not confuse this with the parity of week_since_year_start: if starting_week_type
    # is WeekType.odd, the fourth week of the year will be a WeekType.even,
    # and the one after a WeekType.even
    current_week_type_is_starting_week_type = weeks_since_year_start % 2 != 0
    return (
        starting_week_type
        if current_week_type_is_starting_week_type
        else WeekType.other_one(starting_week_type)
    )
