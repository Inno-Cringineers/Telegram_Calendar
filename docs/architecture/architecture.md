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

| Actor  | Description                                                                |
| ------ | -------------------------------------------------------------------------- |
| User   | Person who interacts with system via TG bot interface                      |
| System | Our personal calendar that store and manage events and throw notifications |

## Component diagram

<div align="center">
<img src="./assets/component_diagram.png">
</div>

| Component          | Layer                  | Responsibilities                                                                                                        |
| ------------------ | ---------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Bot Handler        | Telegram Bot Layer     | Receives messages from Telegram API, routes commands to Command Processor, coordinates with Message Formatter           |
| Command Processor  | Telegram Bot Layer     | Processes user commands, coordinates with Event Manager, Calendar Sync, Daily Plan Manager, and Settings                |
| Message Formatter  | Telegram Bot Layer     | Formats messages for Telegram API output, prepares reminders and notifications                                          |
| Event Manager      | Calendar Service Layer | Manages CRUD operations for events, stores data in database, coordinates with Reminder Scheduler and Daily Plan Manager |
| Reminder Scheduler | Calendar Service Layer | Schedules and sends event reminders, respects quiet hours, formats reminder messages                                    |
| Daily Plan Manager | Calendar Service Layer | Generates and sends daily event summaries, uses user settings for timing and format                                     |
| Calendar Sync      | Integration Layer      | Synchronizes external calendar data, coordinates with ICS Parser and Event Manager                                      |
| ICS Parser         | Integration Layer      | Parses ICS calendar files from external sources, extracts event data                                                    |
| Settings           | Data Layer             | Manages user settings and preferences (timezone, quiet hours, notification frequency)                                   |
| SQLite Database    | Data Layer             | Stores persistent data including events and settings                                                                    |
| Telegram Bot API   | External APIs          | External API for receiving commands and sending messages to users                                                       |
| ICS Calendar Files | External APIs          | External source for calendar data in ICS format                                                                         |

### Sequence diagrams

#### US001

<div align="center">
<img src="./assets/sequence_create_event.png">
</div>

#### US009

<div align="center">
<img src="./assets/sequence_reminder.png">
</div>

#### QAS002

<div align="center">
<img src="./assets/sequence_qas002.png">
</div>

#### QAS007

<div align="center">
<img src="./assets/sequence_qas007.png">
</div>
