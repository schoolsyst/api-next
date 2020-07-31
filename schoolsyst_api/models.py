from datetime import date, datetime, time
from enum import Enum
from typing import *

from pydantic import (
    UUID4,
    BaseModel,
    EmailStr,
    Field,
    PositiveFloat,
    PositiveInt,
    confloat,
    conint,
    constr,
)

Primantissa = confloat(le=1, ge=0)


class Resource(BaseModel):
    """
    Base model for any resource (contains a UUID)
    """

    key: UUID4 = Field(..., alias="_key")


class User(Resource):
    """
    Represents a user
    """

    joined_at: datetime
    username: constr(regex=r"[\w_-]")  # unique
    email: EmailStr  # unique
    email_is_confirmed: bool = False


class DBUser(User):
    password_hash: str


class UserCreation(BaseModel):
    username: constr(regex=r"[\w_-]")
    email: EmailStr
    password: str


class OwnedResouce(Resource):
    """
    Base model for resources owned by users
    """

    owner_id: UUID4
    updated_at: Optional[datetime] = None
    created_at: datetime = datetime.now()


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


class Settings(OwnedResouce):
    theme: ThemeName = ThemeName.auto
    """
    Configures how the year is split.
    For example, for a student whose school works on semesters, the layout will be
    [
        {start: <start of the year>, end: <end of the first semester>},
        {start: <start of the 2nd semester, end: <end of the year>}
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


class Subject(OwnedResouce):
    name: str
    slug: str
    color: conint(ge=0x000000, le=0xFFFFFF) = 0x000000
    weight: PositiveFloat = 1
    goal: Primantissa
    room: str


class Quiz(OwnedResouce):
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


class Note(OwnedResouce):
    name: str = ""
    content: str = ""
    type: NoteType = NoteType.html
    # quizzes: List[Quiz] = []

    @property
    def thumbnail_url(self) -> str:
        return f"/notes/{self.uuid}/thubmnail"


class Grade(OwnedResouce):
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


class Homework(OwnedResouce):
    title: str
    subject_id: UUID4
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


class Event(OwnedResouce):
    subject_id: UUID4
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


class EventMutation(OwnedResouce):
    event_id: Optional[UUID4] = None
    subject_id: Optional[UUID4] = None
    deleted_in: Optional[DateRange] = None
    added_in: Optional[DateRange] = None
    room: Optional[str] = None

    @property
    def interpretation(self) -> Optional[EventMutationInterpretation]:
        """
        if subject_id
           and added_in     and deleted_in      -> edit
           and added_in     and not deleted_in  -> None
           and not added_in and deleted_in      -> None
           and not added_in and not deleted_in  -> None
        else
           and added_in     and deleted_in      -> reschedule
           and added_in     and notdeleted_in   -> edit
           and not added_in and deleted_in      -> deletion
           and not added_in and not deleted_in  -> None

        >>> from uuid import uuid4
        >>> EventMutation(
        ...     uuid=uuid4(),
        ...     owner_id=uuid4(),
        ...     subject_id=uuid4(),
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
        ...     uuid=uuid4(),
        ...     owner_id=uuid4(),
        ...     subject_id=uuid4(),
        ...     added_in=DateRange(
        ...         start=date(2020, 5, 4),
        ...         end=date(2020, 6, 4)
        ...     ),
        ... ).interpretation
        >>> EventMutation(
        ...     uuid=uuid4(),
        ...     owner_id=uuid4(),
        ...     subject_id=uuid4(),
        ...     deleted_in=DateRange(
        ...         start=date(2020, 4, 4),
        ...         end=date(2020, 5, 3)
        ...     )
        ... ).interpretation
        >>> EventMutation(
        ...     uuid=uuid4(),
        ...     owner_id=uuid4(),
        ...     subject_id=uuid4(),
        ... ).interpretation
        >>> EventMutation(
        ...     uuid=uuid4(),
        ...     owner_id=uuid4(),
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
        ...     uuid=uuid4(),
        ...     owner_id=uuid4(),
        ...     added_in=DateRange(
        ...         start=date(2020, 5, 4),
        ...         end=date(2020, 6, 4)
        ...     ),
        ... ).interpretation.value
        'addition'
        >>> EventMutation(
        ...     uuid=uuid4(),
        ...     owner_id=uuid4(),
        ...     deleted_in=DateRange(
        ...         start=date(2020, 4, 4),
        ...         end=date(2020, 5, 3)
        ...     )
        ... ).interpretation.value
        'deletion'
        >>> EventMutation(
        ...     uuid=uuid4(),
        ...     owner_id=uuid4(),
        ... ).interpretation
        """
        if self.subject_id is not None:
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


class Course(OwnedResouce):
    subject_id: UUID4
    start: datetime
    end: datetime
    room: str
