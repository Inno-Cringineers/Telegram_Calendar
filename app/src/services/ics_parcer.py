import icalendar

from models.event import Event


class ICSParser:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_events(self) -> list[Event]:
        with open(self.file_path, "rb") as file:
            calendar = icalendar.Calendar.from_ical(file.read())
        events = []
        for component in calendar.walk():
            if component.name == "VEVENT":
                events.append(
                    Event(
                        title=component.get("summary"),
                        start=component.get("dtstart"),
                        end=component.get("dtend"),
                        description=component.get("description"),
                        rrule=component.get("rrule"),
                        calendar_id=calendar.get("uid"),
                    )
                )
        return events
