from datetime import date, datetime, timedelta
from typing import Optional

from arango.database import StandardDatabase
from fastapi import Depends, Query, status
from fastapi_utils.inferring_router import InferringRouter
from schoolsyst_api import database, settings
from schoolsyst_api.accounts.models import User
from schoolsyst_api.accounts.users import get_current_confirmed_user
from schoolsyst_api.models import DatetimeRange, ObjectBareKey, WeekType
from schoolsyst_api.resource_base import ResourceRoutesGenerator
from schoolsyst_api.schedule import current_week_type
from schoolsyst_api.schedule.models import (
    Course,
    Event,
    EventMutation,
    EventMutationInterpretation,
    InEvent,
)
from schoolsyst_api.settings.models import Settings
from schoolsyst_api.utils import daterange

router = InferringRouter()
helper = ResourceRoutesGenerator(
    name_sg="event", name_pl="events", model_in=InEvent, model_out=Event,
)


@router.get("/weektype_of/{date}")
def get_week_type(date: date, settings: Settings = Depends(settings.get)) -> WeekType:
    return current_week_type(
        starting_week_type=settings.starting_week_type,
        year_start=settings.year_layout[0].start,
        current_date=date,
    )


@router.post("/events/", status_code=status.HTTP_201_CREATED)
def create_event(
    events: InEvent,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Event:
    return helper.create(db, current_user, events)


@router.get("/events/")
def list_events(
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> list[Event]:
    return helper.list(db, current_user)


@router.get("/courses/{start}/{end}/")
def list_courses(
    start: date,
    end: date,
    include: list[EventMutationInterpretation] = Query(
        [
            EventMutationInterpretation.addition,
            EventMutationInterpretation.deletion,
            EventMutationInterpretation.reschedule,
        ]
    ),
    week_types: Optional[list[WeekType]] = Query(None),
    current_user: User = Depends(get_current_confirmed_user),
    settings: Settings = Depends(settings.get),
    db: StandardDatabase = Depends(database.get),
) -> list[Course]:
    """
    {start} is included, {end} is excluded (like python's range())
    """
    end = end or start + timedelta(days=1)
    # Get all of the events
    all_events = [
        batch for batch in db.collection("events").find({"owner_key": current_user.key})
    ]
    all_events: list[Event] = [Event(**event) for event in all_events]
    # Get all of the mutations
    all_mutations = [
        batch
        for batch in db.collection("event_mutations").find(
            {"owner_key": current_user.key}
        )
    ]
    all_mutations: list[EventMutation] = [
        EventMutation(**mutation) for mutation in all_mutations
    ]
    # filter mutations accordinh to ?include
    all_mutations = [
        mutation for mutation in all_mutations if mutation.interpretation in include
    ]

    if week_types == "auto":
        week_types = [get_week_type(start, settings)]

    courses: list[Course] = []
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
                location=event.location,
            )

            # Get relevant mutations:
            mutations = [
                mutation
                for mutation in all_mutations
                if mutation.event_key == event._key
                and (day in mutation.deleted_in or day in mutation.added_in)
            ]

            for mutation in mutations:
                course.location = mutation.location or course.location
                course.subject_key = mutation.subject_key or course.subject_key
                course_daterange = DatetimeRange(start=course.start, end=course.end)
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
def update_event(
    key: ObjectBareKey,
    changes: InEvent,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
) -> Event:
    return helper.update(db, current_user, key, changes)


@router.get("/events/{key}")
def get_event(
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
def delete_event(
    key: ObjectBareKey,
    db: StandardDatabase = Depends(database.get),
    current_user: User = Depends(get_current_confirmed_user),
):
    return helper.delete(db, current_user, key)
