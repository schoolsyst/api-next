from datetime import date, datetime
from enum import auto
from typing import List, Optional

from fastapi_utils.enums import StrEnum
from pydantic import Field, PositiveFloat
from schoolsyst_api.models import BaseModel, DateRange, UserKey, WeekType


class ThemeName(StrEnum):
    light = auto()
    dark = auto()
    auto = auto()


class InSettings(BaseModel):
    """
    Each user has exactly one persistent setting tied to him.
    Thus, the settings' "_key" is the owner user's
    """

    theme: ThemeName = ThemeName.auto
    """
    Configures how the year is split.
    For example, for a student whose school works on semesters, the layout will be
    [
        {start: <start of the year>, end: <end of the first semester>},
        {start: <start of the 2nd semester>, end: <end of the year>}
    ]
    """
    year_layout: List[DateRange] = [
        DateRange(
            start=datetime(datetime.today().year, 1, 1),
            end=datetime(datetime.today().year, 12, 31),
        )
    ]
    """
    Whether the first week of school is an ‘odd’-type week of ‘even’-type.
    """
    starting_week_type: WeekType = WeekType.even
    """
    What unit is used to display grades.
    Note that grades are stored as floats in [0; 1],
    no matter what this value is set to.
    This is solely used for user interfaces.
    """
    grades_unit: PositiveFloat = 100
    """
    Holidays, exceptional weeks without courses, school trips, etc.
    """
    offdays: List[DateRange] = []

    def in_offdays(self, o: date) -> bool:
        return any(o in offday_range for offday_range in self.offdays)


# TODO: autonatic Enum with list of attrs of InSettings as values
class SettingKey(StrEnum):
    theme = auto()
    year_layout = auto()
    starting_week_type = auto()
    grades_unit = auto()
    offdays = auto()


class Settings(InSettings):
    key: UserKey = Field(..., alias="_key")
    updated_at: Optional[datetime] = None
