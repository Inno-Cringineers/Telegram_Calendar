# User Story Priorities

| ID | User Story Name | Feature ID | Priority |
|----|----------------|------------|----------|
| US001 | Create event | F5 | High |
| US002 | Delete event | F5 | High |
| US003 | Update event | F5 | Medium |
| US004 | View event | F7 | Medium |
| US005 | View events | F7 | Medium |
| US006 | Sync external calendar | F4 | Medium |
| US007 | Export calendar | F6 | low |
| US008 | Import calendar | F6 | Medium |
| US009 | Receive reminders | F1 | High |
| US010 | Daily plan | F3 | Medium |
| US011 | Configure quiet hours | F8 | low |
| US012 | Configure timezone | F2 | low |
| US013 | Configure language | F9 | low |
| US014 | Self-host | F10 | High |
| US015 | Single-user restriction | F11 | High |

# User stories

US-001: Create event
- As a user, I want to create an event via the Telegram bot so that the event is added to my personal calendar and reminders are scheduled.
- Acceptance criteria:
    - Bot accepts event title, start time, optional end time, reminder time (which time before event to remind), optional description.
	- Event is persisted and visible in subsequent queries.
	- At least one reminder is scheduled according to user settings.

US-002: Delete event
- As a user, I want to delete an event via the Telegram bot so that the event is deleted from my personal calendar and I no longer receive reminders about this event.
- Acceptance criteria:
	- User can delete an event by id or from a list of events.
	- Deletion removes scheduled reminders and removes event permanently.
	- User receives confirmation of deletion.

US-003: Update event
- As a user, I want to update an existing event's title, start time, end time, reminder time, description so I can correct mistakes or reschedule.
- Acceptance criteria:
 	- User can update an event via bot commands or interactive flow.
 	- Updates persist and any dependent reminders are updated accordingly.
 	- User receives confirmation of successful update and the new reminder schedule.

US-004: View event
- As a user, I want to view event details (including source: calendar/db) so I can confirm event information.
- Acceptance criteria:
 	- User can view event details by id or from a list of events.
 	- Response includes id title, start time, end time, reminder time, description, source (calendar/db).

US-005: View events (list over a period)
- As a user, I want to view a list of events over a period of time so I can inspect my schedule for a given date range.
- Acceptance criteria:
 	- User can request a list of events by specifying a date or a date range (e.g., 07.11.2025, 07.11.2025-11.11.2025).
 	- Response includes events for this period of time with id title, start time, end time, reminder time, description, source (calendar/db).

US-006: Sync external calendar (ical URL)
- As a user, I want the system to import events from an external calendar by ical URL so that my external events appear alongside bot-created events.
- Acceptance criteria:
	- User can provide an .ics URL.
	- Events are parsed and saved without duplicates.
    - Events sync with external calendar
	- Sync reports success/failure and the number of imported events.

US-007 - Export calendar (.ics)
- As a user, I want the system to export events to .ics file so that i can export this file to other service or backup events from bot.
- Acceptance criteria:
	- User can receive .ics file.
	- Internal events (that is stored in db) saved in this file without duplicates.

US-008: Import calendar (.ics)
- As a user, I want the system to import events from .ics file so that i can restore or upload events.
- Acceptance criteria:
	- User can upload .ics file.
	- Events Events are parsed and saved without duplicates.

US-009: Receive reminders
- As a user, I want to receive reminders in Telegram for upcoming events with configured time before event so I don't miss them.
- Acceptance criteria:
	- Reminders are sent within the configured quiet-hours rules and configured reminder time.
	- Reminder messages contain relevant event details.

US-010: Daily plan
- As a user, I want to receive a daily summary of my events so I can review my schedule for the day.
- Acceptance criteria:
	- Summary is delivered at user-configured time.
	- User can see summary list of events for the day.

US-011: Configure quiet hours
- As a user, I want to set quiet-hours so notifications will not be sended at this time.
- Acceptance criteria:
	- Setting persist and apply to all reminders and summaries.
	- Changing setting updates scheduled reminders without requiring re-creation of events.
    - Notification is not sended during quiet-hours

US-012: Configure timezone
- As a user, I want to set timezone so notifications match my timezone.
- Acceptance criteria:
	- Setting persist and apply to all reminders and summaries.
	- Changing setting updates scheduled reminders without requiring re-creation of events.
    - Notification matches user timezone

US-013: Configure language
- As a user, I want to choose english or russian language so notifications will be on chosen language.
- Acceptance criteria:
	- Setting persist and apply to all reminders and summaries.
	- Changing setting updates scheduled reminders without requiring re-creation of events.
    - Notifications sended on chosen language

US-014: Self-host 
- As a user, I want to self-host the calendar bot on my own infrastructure so I maintain full control over my calendar data.
- Acceptance criteria:
 	- Clear setup instructions.
 	- Configuration file template with required settings.
 	- User able to download and setup app.

US-015: Single-user restriction
- As a user, I want the bot to interact exclusively with me (first user) so my calendar remains private and secure.
- Acceptance criteria:
 	- Bot remembers and stores the ID of the first user who interacts with it.
 	- Bot responds only to commands from the registered user ID.
 	- Other users receive a polite message explaining the single-user restriction.
 	- Clear instructions for resetting the registered user if needed.
 	- User ID persistence survives bot restarts.
