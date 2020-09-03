from datetime import datetime, time
from enum import auto
from typing import Optional

from fastapi_utils.enums import StrEnum
from pydantic.color import Color
from schoolsyst_api.models import (
    BaseModel,
    DatetimeRange,
    ISOWeekDay,
    ObjectKey,
    OwnedResource,
)


class InEvent(BaseModel):
    subject_key: Optional[ObjectKey] = None
    title: Optional[str] = None
    color: Optional[Color] = None
    start: time
    end: time
    day: ISOWeekDay
    room: str = ""
    on_even_weeks: bool = True
    on_odd_weeks: bool = True


class Event(OwnedResource, InEvent):
    pass


class EventMutationInterpretation(StrEnum):
    """
    #### edit

    A simple editing of the course, while keeping it on the same day.

    e.g. For the 2019-12-08 Physics course from 08:00 to 08:55,
    the room is L013 and not L453

    #### reschedule

    A rescheduling. The room and other info may also be changed for
    the rescheduled event.

    e.g. The 2019-08-12 Mathematics course from 13:05 to 14:00
    is moved to 2019-08-14 from 08:00 to 08:55

    #### addition

    An exceptional course that is not part of the regular schedule.

    e.g. An exceptional History course will be added at 2019-07-11, from 16:45 to 18:00

    #### deletion

    A removal of course, without rescheduling.

    e.g. The 2020-01-13 Chemistry course from 15:50 to 16:45 is cancelled
    """

    edit = auto()
    reschedule = auto()
    addition = auto()
    deletion = auto()


class EventMutation(OwnedResource):
    event_key: Optional[ObjectKey] = None
    subject_key: Optional[ObjectKey] = None
    deleted_in: Optional[DatetimeRange] = None
    added_in: Optional[DatetimeRange] = None
    room: Optional[str] = None

    @property
    def interpretation(self) -> Optional[EventMutationInterpretation]:
        """
        if subject_key
           and added_in     and deleted_in      -> edit
           and added_in     and not deleted_in  -> None
           and not added_in and deleted_in      -> None
           and not added_in and not deleted_in  -> None
        else
           and added_in     and deleted_in      -> reschedule
           and added_in     and notdeleted_in   -> edit
           and not added_in and deleted_in      -> deletion
           and not added_in and not deleted_in  -> None

        >>> import nanoid
        >>> EventMutation(
        ...     owner_key=userkey(),
        ...     subject_key=objectkey(userkey()),
        ...     added_in=DateRange(
        ...         start=date(2020, 5, 4),
        ...         end=date(2020, 6, 4)
        ...     ),
        ...     deleted_in=DateRange(
        ...         start=date(2020, 4, 4),
        ...         end=date(2020, 5, 3)
        ...     )
        ... ).interpretation.value
        'edit'
        >>> EventMutation(
        ...     owner_key=userkey(),
        ...     subject_key=objectkey(userkey()),
        ...     added_in=DateRange(
        ...         start=date(2020, 5, 4),
        ...         end=date(2020, 6, 4)
        ...     ),
        ... ).interpretation
        >>> EventMutation(
        ...     owner_key=userkey(),
        ...     subject_key=objectkey(userkey()),
        ...     deleted_in=DateRange(
        ...         start=date(2020, 4, 4),
        ...         end=date(2020, 5, 3)
        ...     )
        ... ).interpretation
        >>> EventMutation(
        ...     owner_key=userkey(),
        ...     subject_key=objectkey(userkey()),
        ... ).interpretation
        >>> EventMutation(
        ...     owner_key=userkey(),
        ...     added_in=DateRange(
        ...         start=date(2020, 5, 4),
        ...         end=date(2020, 6, 4)
        ...     ),
        ...     deleted_in=DateRange(
        ...         start=date(2020, 4, 4),
        ...         end=date(2020, 5, 3)
        ...     )
        ... ).interpretation.value
        'reschedule'
        >>> EventMutation(
        ...     owner_key=userkey(),
        ...     added_in=DateRange(
        ...         start=date(2020, 5, 4),
        ...         end=date(2020, 6, 4)
        ...     ),
        ... ).interpretation.value
        'addition'
        >>> EventMutation(
        ...     owner_key=userkey(),
        ...     deleted_in=DateRange(
        ...         start=date(2020, 4, 4),
        ...         end=date(2020, 5, 3)
        ...     )
        ... ).interpretation.value
        'deletion'
        >>> EventMutation(
        ...     owner_key=userkey(),
        ... ).interpretation
        """
        if self.subject_key is not None:
            if self.added_in and self.deleted_in:
                return EventMutationInterpretation.edit
            return None
        if self.added_in and self.deleted_in:
            return EventMutationInterpretation.reschedule
        if self.added_in and not self.deleted_in:
            return EventMutationInterpretation.addition
        if not self.added_in and self.deleted_in:
            return EventMutationInterpretation.deletion
        return None


class Course(OwnedResource):
    subject_key: ObjectKey
    start: datetime
    end: datetime
    room: str
