from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterator, TypeVar

from isodate import duration_isoformat


def make_json_serializable(o: dict) -> dict:
    """
    Turns `o` into a JSON-serializable dict, doing the following conversions:

    - Decimal -> float
    """
    json_serializable = {}
    for key, value in o.items():
        if isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, timedelta):
            value = duration_isoformat(value)
        elif isinstance(value, dict):
            value = make_json_serializable(value)
        json_serializable[key] = value
    return json_serializable


D = TypeVar("D", datetime, date)


def daterange(start: D, end: D, precision: str = "days") -> Iterator[D]:
    """
    Returns a range of datetime objects between start and end.
    The range contains each `precision` between `start` (inclusive) and `end` (exclusive).

    `precision` must be one of: days, seconds, microseconds, weeks.
    """
    # TODO: allow milliseconds, minutes or hours for `precision`
    if precision == "weeks":
        range_of_precision = (end - start).days // 7
    else:
        range_of_precision = getattr(end - start, precision)
    for n in range(int(range_of_precision) + 1):
        if precision == "weeks":
            n *= 7
        yield start + timedelta(**{precision: n})
