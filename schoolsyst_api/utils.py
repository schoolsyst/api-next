from datetime import timedelta
from decimal import Decimal

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
