# Architecture

## Table of Contents

- [Interactive prototype](#interactive-prototype)
- [Context diagram](#context-diagram)
- [Use case diagram](#use-case-diagram)
- [Component diagram](#component-diagram)
- [Sequence diagrams](#sequence-diagrams)

## Interactive prototype

[Link to Figma prototype]

## Context diagram

![Context Diagram](../images/context_diagram.png)

**External actors:**
- User
- Google Calendar
- Outlook Calendar
- Telegram Bot API

## Use case diagram

```plantuml
@startuml
[User] --> (Manage Events)
[User] --> (Configure Reminders)
[User] --> (Sync Calendars)
[User] --> (View Daily Plan)
@enduml
```

**Actors:**
- User

## Component diagram

```plantuml
@startuml
package "Telegram Bot" {
  [Bot Handler]
  [Command Processor]
}

package "Calendar Service" {
  [Event Manager]
  [Reminder Scheduler]
}

package "Integration" {
  [Calendar Sync]
  [ICS Parser]
}

database "Database" {
  [Events]
  [Users]
}

[Bot Handler] --> [Command Processor]
[Command Processor] --> [Event Manager]
[Event Manager] --> [Reminder Scheduler]
[Event Manager] --> [Database]
[Calendar Sync] --> [ICS Parser]
[Calendar Sync] --> [Event Manager]
@enduml
```

**Components:**
- Bot Handler - receives and routes Telegram messages
- Command Processor - processes user commands
- Event Manager - CRUD operations for events
- Reminder Scheduler - manages notification timing
- Calendar Sync - synchronizes external calendars
- ICS Parser - parses iCal format files

### Sequence diagrams

#### User Story: Create Event

```plantuml
@startuml
User -> Bot Handler: /create event
Bot Handler -> Command Processor: parse command
Command Processor -> Event Manager: create event
Event Manager -> Database: save event
Database --> Event Manager: event saved
Event Manager --> Command Processor: success
Command Processor --> Bot Handler: confirmation
Bot Handler --> User: event created
@enduml
```

#### Quality Requirement: Reminder Response Time

```plantuml
@startuml
Reminder Scheduler -> Event Manager: get upcoming events
Event Manager -> Database: query events
Database --> Event Manager: events list
Event Manager --> Reminder Scheduler: events
Reminder Scheduler -> Bot Handler: send notification
Bot Handler -> User: reminder message
@enduml
```

