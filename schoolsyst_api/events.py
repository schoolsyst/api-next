from datetime import date, datetime, timedelta
from typing import List, Optional

from arango.database import StandardDatabase
from fastapi import Depends, Query, status
from fastapi_utils.inferring_router import InferringRouter
from schoolsyst_api import database, settings
from schoolsyst_api.accounts.users import get_current_confirmed_user
from schoolsyst_api.models import (
    Course,
    DatetimeRange,
    Event,
    EventMutation,
    EventMutationInterpretation,
    InEvent,
    ObjectBareKey,
    Settings,
    User,
    WeekType,
)
from schoolsyst_api.resource_base import ResourceRoutesGenerator
from schoolsyst_api.utils import daterange

router = InferringRouter()

helper = ResourceRoutesGenerator(
    name_sg="event", name_pl="events", model_in=InEvent, model_out=Event,
)


def current_week_type(settings: Settings, current_date: date) -> WeekType:
    is_initial_weektype = False
    for i, _ in enumerate(
        daterange(settings.year_layout[0].start, current_date, "weeks")
    ):
        is_initial_weektype = i % 2 == 0

    if is_initial_weektype:
        return settings.starting_week_type
    return (
        WeekType.even if settings.starting_week_type == WeekType.odd else WeekType.odd
    )


@router.get("/weektype_of/{date}")
def get_current_week_type(
    date: date, settings: Settings = Depends(settings.get)
) -> WeekType:
    return current_week_type(settings=settings, current_date=date)


@router.post("/events/", status_code=status.HTTP_201_CREATED)
def create_an_event(
    events: InEvent,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Event:
    return helper.create(db, current_user, events)


@router.get("/events/")
def list_events(
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> List[Event]:
    return helper.list(db, current_user)


@router.get("/courses/{start}/{end}/")
def list_courses_in_date_range(
    start: date,
    end: date,
    include: List[EventMutationInterpretation] = Query(
        [
            EventMutationInterpretation.addition,
            EventMutationInterpretation.deletion,
            EventMutationInterpretation.reschedule,
        ]
    ),
    week_types: Optional[List[WeekType]] = Query(None),
    current_user: User = Depends(get_current_confirmed_user),
    settings: Settings = Depends(settings.get),
    db: StandardDatabase = Depends(database.get),
) -> List[Course]:
    """
    {start} is included, {end} is excluded (like python's range())
    """
    end = end or start + timedelta(days=1)
    # Get all of the events
    all_events = [
        batch for batch in db.collection("events").find({"owner_key": current_user.key})
    ]
    all_events: List[Event] = [Event(**event) for event in all_events]
    # Get all of the mutations
    all_mutations = [
        batch
        for batch in db.collection("event_mutations").find(
            {"owner_key": current_user.key}
        )
    ]
    all_mutations: List[EventMutation] = [
        EventMutation(**mutation) for mutation in all_mutations
    ]
    # filter mutations accordinh to ?include
    all_mutations = [
        mutation for mutation in all_mutations if mutation.interpretation in include
    ]

    if week_types == "auto":
        week_types = [get_current_week_type(start, settings)]

    courses: List[Course] = []
    for day in daterange(start, end, precision="days"):
        # Skip outside of year layout
        if not any(day in year_part for year_part in settings.year_layout):
            continue
        # Skip offdays
        if settings.in_offdays(day):
            continue
        # Get relevant events
        events = [
            event
            for event in all_events
            if (
                # (week_type compliance)
                (event.on_even_weeks and WeekType.even in week_types)
                or (event.on_odd_weeks and WeekType.odd in week_types)
            )
            and (event.day == day)
        ]

        for event in events:
            course = Course(
                start=datetime.combine(date=day, time=event.start),
                end=datetime.combine(date=day, time=event.end),
                subject_key=event.subject_key,
                room=event.room,
            )

            # Get relevant mutations:
            mutations = [
                mutation
                for mutation in all_mutations
                if mutation.event_key == event._key
                and (day in mutation.deleted_in or day in mutation.added_in)
            ]

            for mutation in mutations:
                course.room = mutation.room or course.room
                course.subject_key = mutation.subject_key or course.subject_key
                course_daterange = DatetimeRange(course.start, course.end)
                if mutation.deleted_in:
                    course_daterange ^= mutation.deleted_in
                if mutation.added_in:
                    course_daterange |= mutation.added_in
                if course_daterange.duration:
                    course.start = course_daterange.start
                    course.end = course_daterange.end

            courses += [course]

    return courses


@router.patch("/events/{key}")
def update_an_event(
    key: ObjectBareKey,
    changes: InEvent,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Event:
    return helper.update(db, current_user, key, changes)


@router.get("/events/{key}")
def get_an_event(
    key: ObjectBareKey,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Event:
    return helper.get(db, current_user, key)


delete_an_event_responses = {
    204: {},
    403: {"description": "No event with key {} found"},
    404: {"description": "Currently logged-in user does not own the specified event"},
}


@router.delete(
    "/events/{key}",
    responses=delete_an_event_responses,
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_an_event(
    key: ObjectBareKey,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
):
    return helper.delete(db, current_user, key)
