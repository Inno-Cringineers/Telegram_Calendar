# Plan

## Project goals

Provide to users a tool to create their own planning service (self hosted). Which will Combine notifications from multiple calendars in one place (telegram bot) and provide the opportunity to perform CRUD operations with events and receive reminders centralized from all provided calendars and events.

MVP features have to be done before ITPD Course finish (19.12.2025)

## Threshold of success

- **Time:** Project have to be done before ITPD Course finish (19.12.2025)
- **Budget:** Opensource project (0 rubles)
- **Scope:** The app matches the critical features listed in the Feature Roadmap
- **Quality:** The application meets non-functional requirements and quality attributes

## Feature roadmap

Key Features Identified:

- [ ] Reminders with configurable number of time before an event.
- [ ] Time zones support (manual user setting).
- [ ] A "Daily Plan" feature - a summary of the day's events sent at a user-defined time.
- [ ] Integration with calendars via standardized iCal (ICS) format files.
- [ ] Integration with calendars via OAuth methods (if integratuin via ICS failed)
  - [ ] Outlook
  - [ ] Google
- [ ] Ability to add, edit, and delete events directly within the bot (these events will be stored internally in the bot's database, not synced to external calendars).
- [ ] Users must be able to export their internally-created events, likely in JSON or ICS format, for backup or transfer.
- [ ] Event Viewing: Users will primarily view all events by clicking a provided link that opens their calendar.
- [ ] Notifications are for private chats only. Support for group chats was deferred for future consideration.
- [ ] Quiet Hours: A "Do Not Disturb" feature to mute notifications during specific hours was agreed upon as a useful addition.
- [ ] Write user guides

## Progress monitoring

**Method:** 
**Frequency:** 
**Metrics:** 

## Contingency plans

**Risk 1:** 
**Mitigation:** 

**Risk 2:** 
**Mitigation:** 

