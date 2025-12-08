from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import icalendar
from icalendar.prop import vDDDTypes

from logger.logger import logger


def to_aware_utc(dt, ical_prop=None):
    """
    Convert all ICS dt values to timezone-aware datetime in UTC.
    Handles:
        - datetime with tz
        - naive datetime (checks if original value had Z suffix for UTC)
        - date (floating whole-day events)

    Args:
        dt: datetime or date object to convert
        ical_prop: Optional icalendar property object to check original format
    """

    # All-day date → convert to midnight UTC
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return datetime(dt.year, dt.month, dt.day, tzinfo=UTC)

    # Check if original value had Z suffix (UTC indicator)
    # This is critical because icalendar may parse UTC time as local timezone
    is_utc_format = False
    if ical_prop is not None:
        try:
            # Try to get original ICS format string
            ical_str = ical_prop.to_ical().decode("utf-8") if hasattr(ical_prop, "to_ical") else ""
            # Check if it ends with Z (UTC indicator)
            if ical_str.endswith("Z"):
                is_utc_format = True
            # Also check if property doesn't have TZID parameter (which indicates UTC when Z is present)
            elif hasattr(ical_prop, "params") and "TZID" not in ical_prop.params:
                # If no TZID and the format looks like UTC (has Z in the string representation)
                # This is a fallback check
                pass
        except Exception:
            # If we can't check, fall through to default behavior
            pass

    # Already aware datetime → convert to UTC
    if dt.tzinfo is not None:
        # If original was UTC format (Z suffix), but icalendar returned it with local timezone,
        # we need to reconstruct the UTC time correctly.
        # The problem: icalendar may have interpreted "20251208T070000Z" as "2025-12-08 07:00:00+03:00"
        # (local time), when it should be "2025-12-08 07:00:00+00:00" (UTC).
        # Solution: if original was UTC (Z), take the naive representation and treat it as UTC
        if is_utc_format:
            # Get naive datetime (without timezone info)
            naive_dt = dt.replace(tzinfo=None)
            # Treat it as UTC (since original was UTC)
            return naive_dt.replace(tzinfo=UTC)
        # Normal conversion for non-UTC formats
        return dt.astimezone(UTC)

    # Naive datetime → check if original value had Z suffix (UTC indicator)
    if is_utc_format:
        # Original was UTC, so naive datetime should be interpreted as UTC
        return dt.replace(tzinfo=UTC)

    # Naive datetime → interpret as UTC (ICS standard: floating time is rare)
    return dt.replace(tzinfo=UTC)


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
                    dtstart_prop = event.get("DTSTART")
                    dtend_prop = event.get("DTEND")
                    new_event = VEventSchema(
                        uid=str(event.get("UID")) if event.get("UID") else None,
                        title=str(event.get("SUMMARY")) if event.get("SUMMARY") else None,
                        description=str(event.get("DESCRIPTION")) if event.get("DESCRIPTION") else None,
                        date_start=to_aware_utc(dtstart_prop.dt, dtstart_prop),
                        date_end=to_aware_utc(dtend_prop.dt, dtend_prop),
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
        result.append(to_aware_utc(r.dt))

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
            result.append(to_aware_utc(ex.dt))

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
        return to_aware_utc(trigger.dt, trigger)
    return None
