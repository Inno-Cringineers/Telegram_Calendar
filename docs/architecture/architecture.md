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

<div align="center">
<img src="./assets/context_diagram.png">
</div>

| Actor               | Description                                                                  |
| ------------------- | ---------------------------------------------------------------------------- |
| Calendar ICal       | Calendar API that allow us to get `.ics` files                               |
| Telegram bot API    | Telegram API that allow us to use telegram app as client side for our system |
| User                | Person who interacs with tg bot and also hosting our system                  |
| Software components | Software that user need to install to hosting our system (example: Docker)   |

## Use case diagram

<div align="center">
<img src="./assets/use_case_user.png">
<img src="./assets/use_case_system.png">
</div>

Чтобы не переусложнять диаграмму мы не добавили на нее TG API и Calendar API и нашу систему, т.к. нас интересует только то, как пользователь взаимдодействует с системой.

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

#### Quality Requirement: Reminder Response Time
