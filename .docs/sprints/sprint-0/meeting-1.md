# Meeting date.

meeting started at 31.10.2025 17:27

meeting ended at 31.10.2025 17:55

# Link to the playable recording with sound.

playable recording with sound (meeting_1_at_20251031_172710.m4a) available via the link:

https://drive.google.com/drive/folders/1lFrmgIr-B6MBpstlfxNTnKZliYNLUD5s?usp=drive_link

# Summary of the meeting.

Users: The primary users is common persons. It is a personal calendar tool, not for organization.

Purpose: To build a Telegram bot that pulls events from various calendars and sends reminders.

Open-Source: The project will use the MIT license.

Key Features Identified: 
- Reminders with configurable number of time before an event.
- Time zones support (manual user setting).
- A "Daily Plan" feature - a summary of the day's events sent at a user-defined time.
- Ability to add, edit, and delete events directly within the bot (these events will be stored internally in the bot's database, not synced to external calendars).
- Users must be able to export their internally-created events, likely in JSON or ICS format, for backup or transfer.
- Event Viewing:  Users will primarily view all events by clicking a provided link that opens their calendar.
- Notifications are for private chats only. Support for group chats was deferred for future consideration.
- Quiet Hours: A "Do Not Disturb" feature to mute notifications during specific hours was agreed upon as a useful addition.

User Interface:
- Primary Interface: The Telegram bot (private chat) will be the main user interface.
- Secondary Interface: A minimal web app might be necessary only for the OAuth authentication (only if it will be necessary, to implement OAuth).
 
External Calendar Integration Strategy: 
- Primary Method:  Utilize the standardized iCal (ICS) format. The user provides a private link to their calendar's ICS link, and the bot periodically fetches and parses this file. This method supports any service that provides an ICS link (Google, Outlook, Apple, etc.).
    
- Fallback Method:  If obtaining a private ICS link proves difficult for major providers, a dedicated OAuth integration will be built for Google Calendar and Microsoft Outlook, involving a web app for authentication.

User Guidance: The bot will include guides (e.g., "How to get your Google Calendar ICS link") to facilitate the primary integration method.

Localization: The bot will support both Russian and English.

Technical Architecture & Hosting 
- Deployment: The application must be self-hosted by the end-user using Docker Compose.
- Tech Stack: Main programming language - Python, the database could be MongoDB or PostgreSQL, with a lean towards MongoDB for simplicity. SQLite  was also mentioned as a possibility to avoid a separate database container.

Customer Non-Functional & Future Requirements
- The bot must have high uptime, and reminders must be delivered punctually (with a tolerance of less than one minute of delay).
- Database instances (e.g., MongoDB) must be secured to prevent unauthorized access.
- The architecture should allow new calendar integrations to be added with minimal effort (target: less than one week).

Functional and Non-Functional requirements will be discussed in more detail at the next meeting.

# List of speakers. (Github usernames).

- **Customer** - [deemp](https://github.com/deemp)
- **Main Speaker** - [rikire](https://github.com/rikire)
- **Secondary Speakers**:
  - [Ten-Do](https://github.com/Ten-Do)
  - [03sano30](https://github.com/03sano30)
  - [abdra04-gif](https://github.com/abdra04-gif)

# Transcript of the recording with timestamps and speaker labels.

Transcript of the recording with timestamps and speaker labels (./meeting_1_Transcript/"IT Product_speaker_en_bilingual_timestamps") available via the link:

https://drive.google.com/drive/folders/1lFrmgIr-B6MBpstlfxNTnKZliYNLUD5s?usp=drive_link
