from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import icalendar
from icalendar.prop import vDDDTypes

from logger.logger import logger


@dataclass
class VAlarmSchema:
    description: str | None
    trigger_offset: str | None
    trigger_datetime: datetime | None


@dataclass
class VEventSchema:
    uid: str | None
    title: str | None
    description: str | None
    date_start: datetime
    date_end: datetime
    rrule: str | None
    rdate: list[datetime] | None
    exdate: list[datetime] | None
    alarms: list[VAlarmSchema] | None


class ICSParser:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_schemas(self) -> list[VEventSchema]:
        isc_path = Path(self.file_path)
        icalendar_file = icalendar.Calendar.from_ical(isc_path.read_bytes())  # type: ignore[arg-type]
        schemas: list[VEventSchema] = []
        for event in icalendar_file.walk("VEVENT"):
            if event.name == "VEVENT":
                try:
                    new_event = VEventSchema(
                        uid=str(event.get("UID")) if event.get("UID") else None,
                        title=str(event.get("SUMMARY")) if event.get("SUMMARY") else None,
                        description=str(event.get("DESCRIPTION")) if event.get("DESCRIPTION") else None,
                        date_start=event.get("DTSTART").dt,
                        date_end=event.get("DTEND").dt,
                        rrule=event.get("RRULE").to_ical().decode("utf-8") if event.get("RRULE") else None,
                        rdate=_get_rdates(event) if _get_rdates(event) else None,
                        exdate=_get_exdates(event) if _get_exdates(event) else None,
                        alarms=_extract_alarms(event) if _extract_alarms(event) else None,
                    )
                    schemas.append(new_event)
                except Exception as e:
                    logger.error(f"Error parsing event: {e}", extra={"event": event})
                    continue
        return schemas


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
            VAlarmSchema(
                description=str(alarm.get("DESCRIPTION")) if alarm.get("DESCRIPTION") else None,
                trigger_offset=_get_trigger_offset(alarm) if _get_trigger_offset(alarm) else None,
                trigger_datetime=_get_trigger_datetime(alarm) if _get_trigger_datetime(alarm) else None,
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
