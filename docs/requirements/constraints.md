# System Constraints

| ID    | Constraint                                                                                                                                                                              |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CON-1 | Users must interact with the system through a Telegram bot interface in private chat.                                                                                                   |
| CON-2 | The system must be self-hosted by end-users using Docker Compose.                                                                                                                       |
| CON-3 | The MVP must be delivered by December 19, 2025. Self-hosting setup must be achievable within 40 minutes by a test user following the provided README files.                             |
| CON-4 | The system must synchronize with external calendars via external calendar API that provides iCal (ICS) file (via link)                                                                  |
| CON-5 | The system must support localization in Russian and English languages. All user-facing messages, notifications, and reminders must be available in both languages.                      |
| CON-6 | The system must support single-user per instance. The first user who contacts the bot becomes the primary user, and the bot must only respond to commands from this registered user ID. |
| CON-7 | The project must use the MIT license and be open-source.                                                                                                                                |
| CON-8 | The user can perform CRUD operations only on those events which were not imported from external calendars (created through the bot interface).                                          |
