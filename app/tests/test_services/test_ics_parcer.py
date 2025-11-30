import tempfile
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from icalendar.prop import vDDDTypes, vRecur, vWeekday

from models.event import Event
from models.reminder import Reminder
from services.ics_parcer import ICSParser


@pytest.mark.asyncio
async def test_real_ics_file():
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".ics") as f:
        f.write("""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:abc123
SUMMARY:Real Event
DESCRIPTION:Some description
DTSTART:20250101T120000Z
DTEND:20250101T130000Z
RRULE:FREQ=WEEKLY;COUNT=2
RDATE:20250105T120000Z,20250106T120000Z
EXDATE:20250103T120000Z
BEGIN:VALARM
TRIGGER:-PT30M
REPEAT:2
DURATION:PT10M
DESCRIPTION:Alarm text
END:VALARM
BEGIN:VALARM
TRIGGER:20250101T120000Z
REPEAT:1
DURATION:PT1H
DESCRIPTION:Alarm text 2
END:VALARM
END:VEVENT
END:VCALENDAR
""")

    parser = ICSParser(f.name)

    entities = parser.get_entities()

    assert len(entities) == 1
    event, reminders = entities[0]

    # ------------------ EVENT ------------------
    assert isinstance(event, Event)
    assert event.uid == "abc123"
    assert event.title == "Real Event"
    assert event.description == "Some description"

    assert event.date_start == datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    assert event.date_end == datetime(2025, 1, 1, 13, 0, tzinfo=UTC)

    assert event.rrule == "FREQ=WEEKLY;COUNT=2"

    assert event.rdate == [
        datetime(2025, 1, 5, 12, 0, tzinfo=UTC),
        datetime(2025, 1, 6, 12, 0, tzinfo=UTC),
    ]

    assert event.exdate == [datetime(2025, 1, 3, 12, 0, tzinfo=UTC)]

    # ------------------ VALARM (reminder) ------------------
    assert len(reminders) == 2
    r1 = reminders[0]
    r2 = reminders[1]

    assert isinstance(r1, Reminder)
    assert r1.description == "Alarm text"
    assert r1.repeat_count == 2
    assert r1.repeat_interval == "PT10M"
    assert r1.trigger_datetime is None
    assert r1.trigger_offset == "-PT30M"

    assert isinstance(r2, Reminder)
    assert r2.description == "Alarm text 2"
    assert r2.repeat_count == 1
    assert r2.repeat_interval == "PT1H"
    assert r2.trigger_datetime == datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    assert r2.trigger_offset is None


@pytest.mark.asyncio
async def test_get_entities_single_event():
    parser = ICSParser("fake.ics")

    # ---- MOCK VEVENT ----
    vevent = MagicMock()
    vevent.name = "VEVENT"

    dt_start = vDDDTypes(datetime(2025, 1, 1, 12, 0, tzinfo=UTC))
    dt_end = vDDDTypes(datetime(2025, 1, 1, 13, 0, tzinfo=UTC))
    rrule = vRecur(freq="DAILY", count=3)

    vevent.get.side_effect = lambda key: {
        "UID": "12345",
        "SUMMARY": "Meeting",
        "DESCRIPTION": "Discuss project",
        "DTSTART": dt_start,
        "DTEND": dt_end,
        "RRULE": rrule,
    }.get(key)

    vevent.walk.return_value = []

    # ---- MOCK CALENDAR ----
    calendar_mock = MagicMock()
    calendar_mock.walk.return_value = [vevent]

    with (
        patch("icalendar.Calendar.from_ical", return_value=calendar_mock),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        entities = parser.get_entities()

    assert len(entities) == 1
    event, reminders = entities[0]

    assert isinstance(event, Event)
    assert event.uid == "12345"
    assert event.title == "Meeting"
    assert event.description == "Discuss project"
    assert event.date_start == datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    assert event.date_end == datetime(2025, 1, 1, 13, 0, tzinfo=UTC)
    assert event.rrule == rrule.to_ical().decode("utf-8")
    assert reminders == []


@pytest.mark.asyncio
async def test_rdate_exdate_extraction():
    parser = ICSParser("fake.ics")

    vevent = MagicMock()
    vevent.name = "VEVENT"

    rdate_values = MagicMock()
    rdate_values.dts = [
        vDDDTypes(datetime(2025, 1, 2, tzinfo=UTC)),
        vDDDTypes(datetime(2025, 1, 3, tzinfo=UTC)),
    ]

    exdate_values = MagicMock()
    exdate_values.dts = [
        vDDDTypes(datetime(2025, 1, 4, tzinfo=UTC)),
    ]

    dt_start = vDDDTypes(datetime(2025, 1, 1, tzinfo=UTC))
    dt_end = vDDDTypes(datetime(2025, 1, 1, 1, tzinfo=UTC))

    vevent.get.side_effect = lambda key: {
        "UID": "uid",
        "SUMMARY": "Test",
        "DTSTART": dt_start,
        "DTEND": dt_end,
        "DESCRIPTION": None,
        "RRULE": None,
        "RDATE": rdate_values,
        "EXDATE": exdate_values,
    }.get(key)

    vevent.walk.return_value = []

    calendar_mock = MagicMock()
    calendar_mock.walk.return_value = [vevent]

    with (
        patch("icalendar.Calendar.from_ical", return_value=calendar_mock),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        entities = parser.get_entities()

    event, _ = entities[0]

    assert event.rdate == [datetime(2025, 1, 2, tzinfo=UTC), datetime(2025, 1, 3, tzinfo=UTC)]

    assert event.exdate == [datetime(2025, 1, 4, tzinfo=UTC)]

    assert event.date_start == datetime(2025, 1, 1, tzinfo=UTC)
    assert event.date_end == datetime(2025, 1, 1, 1, tzinfo=UTC)


@pytest.mark.asyncio
async def test_extract_alarms():
    parser = ICSParser("fake.ics")

    # ---- VALARM ----
    valarm = MagicMock()
    valarm.get.side_effect = lambda key: {
        "DESCRIPTION": "Reminder text",
        "REPEAT": 3,
        "DURATION": vDDDTypes(timedelta(minutes=10)),
        "TRIGGER": vDDDTypes(timedelta(minutes=-15)),
    }.get(key)

    # ---- VEVENT ----
    vevent = MagicMock()
    vevent.name = "VEVENT"
    vevent.get.side_effect = lambda key: {
        "UID": "1",
        "SUMMARY": "Event",
        "DTSTART": vDDDTypes(datetime(2025, 1, 1, 12, 0, tzinfo=UTC)),
        "DTEND": vDDDTypes(datetime(2025, 1, 1, 13, 0, tzinfo=UTC)),
    }.get(key)

    vevent.walk.return_value = [valarm]

    calendar_mock = MagicMock()
    calendar_mock.walk.return_value = [vevent]

    with (
        patch("icalendar.Calendar.from_ical", return_value=calendar_mock),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        entities = parser.get_entities()

    _, reminders = entities[0]

    assert len(reminders) == 1
    r = reminders[0]
    assert isinstance(r, Reminder)
    assert r.description == "Reminder text"
    assert r.repeat_count == 3
    assert r.repeat_interval == "PT10M"
    assert r.trigger_offset == "-PT15M"


@pytest.mark.asyncio
async def test_trigger_datetime():
    parser = ICSParser("fake.ics")

    abs_trigger = vDDDTypes(datetime(2025, 5, 5, 10, 0, tzinfo=UTC))

    valarm = MagicMock()
    valarm.get.side_effect = lambda key: {
        "TRIGGER": abs_trigger,
    }.get(key)

    vevent = MagicMock()
    vevent.name = "VEVENT"
    vevent.get.side_effect = lambda key: {
        "UID": "1",
        "SUMMARY": "Event",
        "DTSTART": vDDDTypes(datetime(2025, 1, 1, 12, 0, tzinfo=UTC)),
        "DTEND": vDDDTypes(datetime(2025, 1, 1, 13, 0, tzinfo=UTC)),
    }.get(key)
    vevent.walk.return_value = [valarm]

    calendar_mock = MagicMock()
    calendar_mock.walk.return_value = [vevent]

    with (
        patch("icalendar.Calendar.from_ical", return_value=calendar_mock),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        entities = parser.get_entities()

    _, reminders = entities[0]

    assert reminders[0].trigger_datetime == datetime(2025, 5, 5, 10, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_multiple_vevents():
    parser = ICSParser("fake.ics")

    ve1 = MagicMock()
    ve1.name = "VEVENT"
    ve1.get.side_effect = lambda key: {
        "UID": "ev1",
        "SUMMARY": "Event 1",
        "DESCRIPTION": None,
        "DTSTART": vDDDTypes(datetime(2025, 1, 1, tzinfo=UTC)),
        "DTEND": vDDDTypes(datetime(2025, 1, 1, 1, tzinfo=UTC)),
        "RRULE": None,
        "RDATE": None,
        "EXDATE": None,
    }.get(key)
    ve1.walk.return_value = []

    ve2 = MagicMock()
    ve2.name = "VEVENT"
    ve2.get.side_effect = lambda key: {
        "UID": "ev2",
        "SUMMARY": "Event 2",
        "DESCRIPTION": "desc2",
        "DTSTART": vDDDTypes(datetime(2025, 2, 2, tzinfo=UTC)),
        "DTEND": vDDDTypes(datetime(2025, 2, 2, 1, tzinfo=UTC)),
        "RRULE": vRecur(freq="WEEKLY"),
        "RDATE": None,
        "EXDATE": None,
    }.get(key)
    ve2.walk.return_value = []

    calendar_mock = MagicMock()
    calendar_mock.walk.return_value = [ve1, ve2]

    with (
        patch("icalendar.Calendar.from_ical", return_value=calendar_mock),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        entities = parser.get_entities()

    assert len(entities) == 2
    assert entities[0][0].uid == "ev1"
    assert entities[1][0].uid == "ev2"


@pytest.mark.asyncio
async def test_exdate_multiple_properties():
    parser = ICSParser("fake.ics")

    ex1 = MagicMock()
    ex1.dts = [
        vDDDTypes(datetime(2025, 1, 1, tzinfo=UTC)),
    ]

    ex2 = MagicMock()
    ex2.dts = [
        vDDDTypes(datetime(2025, 1, 2, tzinfo=UTC)),
        vDDDTypes(datetime(2025, 1, 3, tzinfo=UTC)),
    ]

    vevent = MagicMock()
    vevent.name = "VEVENT"
    vevent.get.side_effect = lambda key: {
        "UID": "uid",
        "SUMMARY": "e",
        "DTSTART": vDDDTypes(datetime(2025, 1, 1, tzinfo=UTC)),
        "DTEND": vDDDTypes(datetime(2025, 1, 1, 1, tzinfo=UTC)),
        "EXDATE": [ex1, ex2],
    }.get(key)
    vevent.walk.return_value = []

    calendar_mock = MagicMock()
    calendar_mock.walk.return_value = [vevent]

    with (
        patch("icalendar.Calendar.from_ical", return_value=calendar_mock),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        (event, _) = parser.get_entities()[0]

    assert event.exdate == [
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 1, 2, tzinfo=UTC),
        datetime(2025, 1, 3, tzinfo=UTC),
    ]


def test_rdate_multiple():
    parser = ICSParser("fake.ics")

    rdate = MagicMock()
    rdate.dts = [
        vDDDTypes(datetime(2025, 5, 10, tzinfo=UTC)),
        vDDDTypes(datetime(2025, 5, 11, tzinfo=UTC)),
    ]

    vevent = MagicMock()
    vevent.name = "VEVENT"
    vevent.get.side_effect = lambda key: {
        "UID": "u",
        "SUMMARY": "s",
        "DTSTART": vDDDTypes(datetime(2025, 5, 1, tzinfo=UTC)),
        "DTEND": vDDDTypes(datetime(2025, 5, 1, 2, tzinfo=UTC)),
        "RDATE": rdate,
    }.get(key)
    vevent.walk.return_value = []

    calendar_mock = MagicMock()
    calendar_mock.walk.return_value = [vevent]

    with (
        patch("icalendar.Calendar.from_ical", return_value=calendar_mock),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        event, _ = parser.get_entities()[0]

    assert event.rdate == [
        datetime(2025, 5, 10, tzinfo=UTC),
        datetime(2025, 5, 11, tzinfo=UTC),
    ]


def test_rrule_extraction():
    parser = ICSParser("fake.ics")

    vevent = MagicMock()
    vevent.name = "VEVENT"
    vevent.get.side_effect = lambda key: {
        "UID": "1",
        "SUMMARY": "A",
        "DTSTART": vDDDTypes(datetime(2025, 1, 1, tzinfo=UTC)),
        "DTEND": vDDDTypes(datetime(2025, 1, 1, 1, tzinfo=UTC)),
        "RRULE": vRecur(
            freq="DAILY",
            byday=[vWeekday("MO"), vWeekday("WE"), vWeekday("FR")],
            count=10,
        ),
    }.get(key)
    vevent.walk.return_value = []

    calendar_mock = MagicMock()
    calendar_mock.walk.return_value = [vevent]

    with (
        patch("icalendar.Calendar.from_ical", return_value=calendar_mock),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        event, _ = parser.get_entities()[0]

    assert event.rrule == vRecur(
        freq="DAILY", byday=[vWeekday("MO"), vWeekday("WE"), vWeekday("FR")], count=10
    ).to_ical().decode("utf-8")


def test_trigger_offset():
    parser = ICSParser("fake.ics")

    valarm = MagicMock()
    valarm.get.side_effect = lambda key: {
        "TRIGGER": vDDDTypes(timedelta(minutes=-30)),
    }.get(key)

    vevent = MagicMock()
    vevent.name = "VEVENT"
    vevent.get.side_effect = lambda k: {
        "UID": "1",
        "SUMMARY": "E",
        "DTSTART": vDDDTypes(datetime(2025, 1, 1, tzinfo=UTC)),
        "DTEND": vDDDTypes(datetime(2025, 1, 1, 1, tzinfo=UTC)),
    }.get(k)
    vevent.walk.return_value = [valarm]

    calendar_mock = MagicMock()
    calendar_mock.walk.return_value = [vevent]

    with (
        patch("icalendar.Calendar.from_ical", return_value=calendar_mock),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        _, reminders = parser.get_entities()[0]

    assert reminders[0].trigger_offset == "-PT30M"


def test_trigger_datetime_absolute():
    parser = ICSParser("fake.ics")

    valarm = MagicMock()
    valarm.get.side_effect = lambda key: {
        "DESCRIPTION": "Alarm text",
        "REPEAT": None,
        "DURATION": None,
        "TRIGGER": vDDDTypes(datetime(2026, 6, 6, 10, 0, tzinfo=UTC)),
    }.get(key)

    vevent = MagicMock()
    vevent.name = "VEVENT"
    vevent.get.side_effect = lambda k: {
        "UID": "1",
        "SUMMARY": "E",
        "DTSTART": vDDDTypes(datetime(2026, 6, 1, tzinfo=UTC)),
        "DTEND": vDDDTypes(datetime(2026, 6, 1, 1, tzinfo=UTC)),
    }.get(k)
    vevent.walk.return_value = [valarm]

    calendar_mock = MagicMock()
    calendar_mock.walk.return_value = [vevent]

    with (
        patch("icalendar.Calendar.from_ical", return_value=calendar_mock),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        _, reminders = parser.get_entities()[0]

    assert reminders[0].trigger_datetime == datetime(2026, 6, 6, 10, 0, tzinfo=UTC)


def test_trigger_invalid_type():
    parser = ICSParser("fake.ics")

    valarm = MagicMock()
    valarm.get.side_effect = lambda key: {
        "TRIGGER": "invalid_trigger",
    }.get(key)

    vevent = MagicMock()
    vevent.name = "VEVENT"
    vevent.get.side_effect = lambda k: {
        "UID": "1",
        "SUMMARY": "E",
        "DTSTART": vDDDTypes(datetime(2026, 1, 1, tzinfo=UTC)),
        "DTEND": vDDDTypes(datetime(2026, 1, 1, 1, tzinfo=UTC)),
    }.get(k)
    vevent.walk.return_value = [valarm]

    calendar_mock = MagicMock()
    calendar_mock.walk.return_value = [vevent]

    with (
        patch("icalendar.Calendar.from_ical", return_value=calendar_mock),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        _, reminders = parser.get_entities()[0]

    assert reminders[0].trigger_offset is None
    assert reminders[0].trigger_datetime is None


def test_multiple_valarms():
    parser = ICSParser("fake.ics")

    a1 = MagicMock()
    a1.get.side_effect = lambda key: {"DESCRIPTION": "A1", "TRIGGER": vDDDTypes(timedelta(minutes=-10))}.get(key)

    a2 = MagicMock()
    a2.get.side_effect = lambda key: {"DESCRIPTION": "A2", "TRIGGER": vDDDTypes(timedelta(minutes=-20))}.get(key)

    vevent = MagicMock()
    vevent.name = "VEVENT"
    vevent.get.side_effect = lambda k: {
        "UID": "1",
        "SUMMARY": "E",
        "DTSTART": vDDDTypes(datetime(2025, 1, 1, tzinfo=UTC)),
        "DTEND": vDDDTypes(datetime(2025, 1, 1, 1, tzinfo=UTC)),
    }.get(k)
    vevent.walk.return_value = [a1, a2]

    calendar_mock = MagicMock()
    calendar_mock.walk.return_value = [vevent]

    with (
        patch("icalendar.Calendar.from_ical", return_value=calendar_mock),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        _, reminders = parser.get_entities()[0]

    assert len(reminders) == 2
    assert reminders[0].description == "A1"
    assert reminders[1].description == "A2"


def test_missing_dtstart():
    parser = ICSParser("fake.ics")

    vevent = MagicMock()
    vevent.name = "VEVENT"
    vevent.get.side_effect = lambda k: {
        "UID": "1",
        "SUMMARY": "E",
        "DTEND": vDDDTypes(datetime(2025, 1, 1, 1, tzinfo=UTC)),
    }.get(k)
    vevent.walk.return_value = []

    calendar_mock = MagicMock()
    calendar_mock.walk.return_value = [vevent]

    with (
        patch("icalendar.Calendar.from_ical", return_value=calendar_mock),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        event, _ = parser.get_entities()[0]

    assert event.date_start is None


def test_invalid_ics_file():
    parser = ICSParser("fake.ics")

    with (
        patch("icalendar.Calendar.from_ical", side_effect=ValueError("ICS broken")),
        patch("pathlib.Path.read_bytes", return_value=b"dummy"),
    ):
        with pytest.raises(ValueError):
            _ = parser.get_entities()
