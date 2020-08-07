from datetime import date, datetime, time
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Set, Union

import nanoid
from pydantic import BaseModel as PydanticBaseModel
from pydantic import EmailStr, Field, PositiveFloat, PositiveInt, confloat, constr
from pydantic.color import Color
from slugify import slugify

Primantissa = confloat(le=1, ge=0)
ID_CHARSET = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
USER_KEY_LEN = 10
OBJECT_KEY_LEN = 6
UserKey = constr(regex=f"[{ID_CHARSET}]{{{USER_KEY_LEN}}}")
ObjectKey = constr(
    regex=f"[{ID_CHARSET}]{{{USER_KEY_LEN}}}:[{ID_CHARSET}]{{{OBJECT_KEY_LEN}}}"
)
ObjectBareKey = constr(regex=f"[{ID_CHARSET}]{{{OBJECT_KEY_LEN}}}")


def userkey():
    return nanoid.generate(ID_CHARSET, USER_KEY_LEN)


def objectbarekey():
    return nanoid.generate(ID_CHARSET, OBJECT_KEY_LEN)


def objectkey(owner_key):
    return f"{owner_key}:{objectbarekey()}"


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
        include: Set[str] = None,
        exclude: Set[str] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> Dict[str, Any]:
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
        include |= {"_key"}
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


UsernameStr = constr(regex=r"[\w_-]+")


class User(BaseModel):
    """
    Represents a user
    """

    key: UserKey = Field(userkey(), alias="_key")
    joined_at: datetime
    username: UsernameStr  # unique
    email: EmailStr  # unique
    email_is_confirmed: bool = False


class DBUser(User):
    password_hash: str


class InUser(BaseModel):
    username: UsernameStr
    email: EmailStr
    password: str


class OwnedResource(BaseModel):
    """
    Base model for resources owned by users
    """

    object_key: ObjectBareKey
    owner_key: UserKey
    updated_at: Optional[datetime] = None
    created_at: datetime = datetime.now()

    @property
    def _key(self) -> ObjectKey:
        return f"{self.owner_key}:{self.object_key}"


class DatetimeRange(BaseModel):
    start: datetime
    end: datetime


class DateRange(BaseModel):
    start: date
    end: date


class ThemeName(str, Enum):
    light = "light"
    dark = "dark"
    auto = "auto"


class WeekType(str, Enum):
    even = "even"
    odd = "odd"


class Settings(OwnedResource):
    theme: ThemeName = ThemeName.auto
    """
    Configures how the year is split.
    For example, for a student whose school works on semesters, the layout will be
    [
        {start: <start of the year>, end: <end of the first semester>},
        {start: <start of the 2nd semester>, end: <end of the year>}
    ]
    """
    year_layout: List[DateRange]
    """
    Whether the first week of school is an ‘odd’-type week of ‘even’-type.
    """
    starting_week_type: WeekType = WeekType.even
    """
    What unit is used to display grades.
    Note that grades are stored as floats in [0; 1],
    no matter what this value is set to.
    """
    grades_unit: Union[PositiveFloat, PositiveInt]
    """
    Holidays, exceptional weeks without courses, school trips, etc.
    """
    offdays: List[DateRange] = []


class InSubject(BaseModel):
    name: str
    color: Color
    weight: Union[PositiveFloat, Literal[0]] = 1.0
    goal: Primantissa
    room: str

    @property
    def slug(self) -> str:  # unique
        return slugify(self.name)


class Subject(InSubject, OwnedResource):
    pass


class Quiz(OwnedResource):
    name: str
    # questions: List[Question] = []
    # Number of trials in test mode
    tries_test: PositiveInt = 0
    # Number of trials in train mode
    tries_train: PositiveInt = 0
    # Total number of trials
    tries_total: PositiveInt = 0
    # (in seconds) the total time spent on this quizz
    time_spent: PositiveInt = 0
    # sessions: List[QuizSession] = []


class NoteType(str, Enum):
    html = "html"
    markdown = "markdown"
    asciidoc = "asciidoc"
    external = "external"


class NoteContentType(str, Enum):
    pdf = "pdf"
    tex = "tex"
    docx = "docx"
    txt = "txt"
    odt = "odt"
    markdown = "markdown"
    asciidoc = "asciidoc"
    rst = "rst"
    epub = "epub"
    mediawiki = "mediawiki"


class Note(OwnedResource):
    name: str = ""
    content: str = ""
    type: NoteType = NoteType.html
    # quizzes: List[Quiz] = []

    @property
    def thumbnail_url(self) -> str:
        return f"/notes/{self._key}/thubmnail"


class Grade(OwnedResource):
    title: str
    actual: Optional[Primantissa] = None
    expected: Optional[Primantissa] = None
    goal: Optional[Primantissa] = None
    unit: confloat(gt=0)
    weight: PositiveFloat = 1
    obtained_at: Optional[datetime] = None


class HomeworkType(str, Enum):
    test = "test"
    coursework = "coursework"
    to_bring = "to_bring"
    exercise = "exercise"


class Homework(OwnedResource):
    title: str
    subject_key: ObjectKey
    type: HomeworkType
    completed_at: datetime
    progress: Primantissa
    notes: List[Note] = []
    grades: List[Grade] = []


class ISOWeekDay(int, Enum):
    monday = 1
    tuesday = 2
    wednesday = 3
    thursday = 4
    friday = 5
    saturday = 6
    sunday = 7


class Event(OwnedResource):
    subject_key: ObjectKey
    start: time
    end: time
    day: ISOWeekDay
    room: str = ""
    on_even_weeks: bool = True
    on_odd_weeks: bool = True


class EventMutationInterpretation(str, Enum):
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

    edit = "edit"
    reschedule = "reschedule"
    addition = "addition"
    deletion = "deletion"


class EventMutation(OwnedResource):
    event_key: Optional[ObjectKey] = None
    subject_key: Optional[ObjectKey] = None
    deleted_in: Optional[DateRange] = None
    added_in: Optional[DateRange] = None
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
