from datetime import datetime, timedelta
from pathlib import Path

import icalendar
from icalendar.prop import vDDDTypes

from models.event import Event
from models.reminder import Reminder


class ICSParser:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_entities(self) -> list[tuple[Event, list[Reminder]]]:
        isc_path = Path(self.file_path)
        icalendar_file = icalendar.Calendar.from_ical(isc_path.read_bytes())  # type: ignore[arg-type]
        entities = []
        for event in icalendar_file.walk("VEVENT"):
            if event.name == "VEVENT":
                new_event = Event(
                    uid=str(event.get("UID")) if event.get("UID") else None,
                    title=str(event.get("SUMMARY")) if event.get("SUMMARY") else None,
                    description=str(event.get("DESCRIPTION")) if event.get("DESCRIPTION") else None,
                    date_start=event.get("DTSTART").dt if event.get("DTSTART") else None,
                    date_end=event.get("DTEND").dt if event.get("DTEND") else None,
                    rrule=event.get("RRULE").to_ical().decode("utf-8") if event.get("RRULE") else None,
                    rdate=_get_rdates(event),
                    exdate=_get_exdates(event),
                )
                entities.append((new_event, _extract_alarms(event)))
        return entities


def _get_rdates(component):
    rdate_prop = component.get("RDATE")
    if not rdate_prop:
        return None

    result = []
    for r in rdate_prop.dts:
        result.append(r.dt)

    return result


def _get_exdates(component):
    exdate_props = component.get("EXDATE")
    if not exdate_props:
        return None

    result = []

    if not isinstance(exdate_props, list):
        exdate_props = [exdate_props]

    for exprop in exdate_props:
        for ex in exprop.dts:
            result.append(ex.dt)

    return result


def _extract_alarms(event):
    alarms = []
    for alarm in event.walk("VALARM"):
        alarms.append(
            Reminder(
                description=str(alarm.get("DESCRIPTION")) if alarm.get("DESCRIPTION") else None,
                repeat_count=int(alarm.get("REPEAT")) if alarm.get("REPEAT") else None,
                repeat_interval=alarm.get("DURATION").to_ical().decode("utf-8") if alarm.get("DURATION") else None,
                trigger_offset=_get_trigger_offset(alarm),
                trigger_datetime=_get_trigger_datetime(alarm),
            )
        )
    return alarms


def _get_trigger_offset(alarm):
    trigger = alarm.get("TRIGGER")
    if trigger is None:
        return None
    if isinstance(trigger, vDDDTypes) and isinstance(trigger.dt, timedelta):
        return trigger.to_ical().decode("utf-8")
    return None


def _get_trigger_datetime(alarm):
    trigger = alarm.get("TRIGGER")
    if trigger is None:
        return None
    if isinstance(trigger, vDDDTypes) and isinstance(trigger.dt, datetime):
        return trigger.dt
    return None
