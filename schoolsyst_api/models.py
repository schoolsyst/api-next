"""
Models for both the API's JSON interface and the database's documents.

Some prefixes to the model's names indicate particular variants of that model:

- "In" — fields required for the creation of an object (via POST)
- "DB" — model of the document stored in the database
- ""
"""
from datetime import date, datetime, timedelta
from enum import Enum, auto
from typing import Any, Optional, Union

import nanoid
from fastapi_utils.enums import StrEnum
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, confloat, constr

# Misc. pydantic constrained types

Primantissa = confloat(le=1, ge=0)

# Keys

ID_CHARSET = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
USER_KEY_LEN = 10
OBJECT_KEY_LEN = 6
UserKey = constr(regex=f"[{ID_CHARSET}]{{{USER_KEY_LEN}}}")
ObjectKey = constr(
    regex=f"[{ID_CHARSET}]{{{USER_KEY_LEN}}}:[{ID_CHARSET}]{{{OBJECT_KEY_LEN}}}"
)
ObjectBareKey = constr(regex=f"[{ID_CHARSET}]{{{OBJECT_KEY_LEN}}}")
OBJECT_KEY_FORMAT = "{owner}:{object}"


def userkey():
    """
    Generates a new nanoid for use with user keys.
    """
    return nanoid.generate(ID_CHARSET, USER_KEY_LEN)


def objectbarekey():
    """
    Generates a new nanoid for use with object bare keys.
    """
    return nanoid.generate(ID_CHARSET, OBJECT_KEY_LEN)


def objectkey(owner_key):
    """
    Given an owner key, generates a new nanoid for use with object keys.
    """
    return OBJECT_KEY_FORMAT.format(owner=owner_key, object=objectbarekey())


class BaseModel(PydanticBaseModel):
    """
    Workaround for serializing properties with pydantic until
    https://github.com/samuelcolvin/pydantic/issues/935
    is solved

    Credits: https://github.com/samuelcolvin/pydantic/issues/935#issuecomment-641175527
    """

    @classmethod
    def get_properties(cls):
        return [
            prop
            for prop in dir(cls)
            if isinstance(getattr(cls, prop), property)
            and prop not in ("__values__", "fields")
        ]

    def dict(
        self,
        *,
        include: set[str] = None,
        exclude: set[str] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> dict[str, Any]:
        attribs = super().dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        include = include or set()
        include |= {
            "_key",
            "slug",
            "completed",
            "late",
            "progress",
            "progress_from_tasks",
        }
        props = self.get_properties()
        # Include and exclude properties
        if include:
            props = [prop for prop in props if prop in include]
        if exclude:
            props = [prop for prop in props if prop not in exclude]

        # Update the attribute dict with the properties
        if props:
            attribs.update({prop: getattr(self, prop) for prop in props})

        return attribs


class OwnedResource(BaseModel):
    """
    Base model for resources owned by users
    """

    object_key: ObjectBareKey = Field(default_factory=objectbarekey)
    owner_key: UserKey
    updated_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def _key(self) -> ObjectKey:
        return f"{self.owner_key}:{self.object_key}"


class DateRange(BaseModel):
    """
    `start` is inclusive, `end` is exclusive.
    (just like python's `range()`)
    """

    start: date
    end: date

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    def __contains__(self, o: Union[date, "DateRange"]) -> bool:
        if isinstance(o, date):
            return self.start <= o < self.end
        return self.start <= o.start and self.end >= o.end

    def __xor__(self, o: "DateRange") -> "DateRange":
        return DateRange(
            start=o.start if o.start >= self.start else self.start,
            end=o.end if o.end >= self.end else self.end,
        )

    def __or__(self, o: "DateRange") -> "DateRange":
        return DateRange(
            start=o.start if o.start <= self.start else self.start,
            end=o.end if o.end >= self.end else self.end,
        )


class DatetimeRange(DateRange):
    """
    A DateRange, but with `datetime` objects instead of simple dates.
    """

    start: datetime
    end: datetime


class WeekType(StrEnum):
    """
    Different week types, used for schools that change their schedule every other week.
    """

    even = auto()
    odd = auto()


class ISOWeekDay(int, Enum):
    """
    Days of the week as numbers, as defined by ISO 8601.
    """

    monday = 1
    tuesday = 2
    wednesday = 3
    thursday = 4
    friday = 5
    saturday = 6
    sunday = 7
