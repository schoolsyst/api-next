from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from tempfile import TemporaryFile
from typing import Iterator, TypeVar
from zipfile import ZipFile

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

# TODO: instead of those three functions, a daterange class,
# and date_in_range could be implemented as __in__ (as well as do_dateranges_overlap)


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


def zip_text(text: str, filename: str) -> bytes:
    # Open StringIO to grab in-memory ZIP contents
    buffer = BytesIO()
    file = ZipFile(buffer, "w")

    with TemporaryFile("w") as temp_file:
        # Write the contents from text into a temprary file
        temp_file.write(text)
        # Write that zip file into the archive
        file.write(temp_file.name, filename)

    # Close the archive
    file.close()

    return buffer.getvalue()
