<p align="center">
  <img src="./images/Banner.png"/>
</p>

# Personal Calendar Reminder &middot; ![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)
A telegram bot as a frontend for the joint calendar and calendar synchronization plugins that can go and collect info from your calendars.

## Project goal
Give users a tool to create their own planning service (self hosted). which will allow you to perform event CRUD operations through the telegram bot interface and receive reminders.

## Threshold of Success
- **Time:** Project have to be done before ITPD Course finish (19.12.2025)
- **Budget:** Opensource project (0 rubles)
- **Scope:**: The app matches the critical features listed in the Feature Roadmap
- **Quality:**: The application meets non-functional requirements and quality attributes

## Description
The project is a self-hosted solution that allows the user to run it on their server and get a service for working with events and reminders. User gets the opportunity to perform CRUD operations on events through the interface of the telegram bot. The service allows you to integrate data from existing calendars (Google, Outlook).

## Reminder Context Diagram
![Context diagram](./images/context_diagram.png)

## Feature Roadmap
Key Features Identified: 
- [ ] Reminders with configurable number of time before an event.
- [ ] Time zones support (manual user setting).
- [ ] A "Daily Plan" feature - a summary of the day's events sent at a user-defined time.
- [ ] Integration with calendars via standardized iCal (ICS) format files.
- [ ] Integration with calendars via OAuth methods
    - [ ] Outlook
    - [ ] Google
- [ ] Ability to add, edit, and delete events directly within the bot (these events will be stored internally in the bot's database, not synced to external calendars).
- [ ] Users must be able to export their internally-created events, likely in JSON or ICS format, for backup or transfer.
- [ ] Event Viewing:  Users will primarily view all events by clicking a provided link that opens their calendar.
- [ ] Notifications are for private chats only. Support for group chats was deferred for future consideration.
- [ ] Quiet Hours: A "Do Not Disturb" feature to mute notifications during specific hours was agreed upon as a useful addition.
- [ ] Write user guides


# Documentation

will be soon - user guides will be added when project will be created

# Links
- [Sprints](https://your-website.com/docs/sprints) - information about meetings with the customer and meeting reports
- [AI usage](https://your-website.com/docs/ai-usage.md) - how we use AI in this project.