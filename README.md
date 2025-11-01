<p align="center">
  <img src="./images/Banner.png"/>
</p>

# Personal Calendar Reminder &middot; ![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)
A telegram bot as a frontend for the joint calendar and calendar synchronization plugins that can go and collect info from your calendars.

## Project goal
Provide to users a tool to create their own planning service (self hosted). Which will Combine notifications from multiple calendars in one place (telegram bot) and provide the opportunity to perform CRUD operations with events and receive reminders centralized from all provided calendars and events.

MVP features have to be done before ITPD Course finish (19.12.2025) 

## Threshold of Success
- **Time:** Project have to be done before ITPD Course finish (19.12.2025)
- **Budget:** Opensource project (0 rubles)
- **Scope:**: The app matches the critical features listed in the Feature Roadmap
- **Quality:**: The application meets non-functional requirements and quality attributes

## Description
The project is a self-hosted solution that allows the user to run it on their server and get a service for working with events and reminders. User gets the opportunity to perform CRUD operations on events through the interface of the telegram bot. The telegram bot will notify the user about upcoming events at the frequency specified by the user, and send plans for the day. The service allows you to integrate data from existing calendars (Google, Outlook). 

## Reminder Context Diagram
<div style="display: flex; justify-content: center; background: white; padding: 6px;">
<img src="./images/context_diagram.png">
</div>

## Feature Roadmap
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
- [ ] Event Viewing:  Users will primarily view all events by clicking a provided link that opens their calendar.
- [ ] Notifications are for private chats only. Support for group chats was deferred for future consideration.
- [ ] Quiet Hours: A "Do Not Disturb" feature to mute notifications during specific hours was agreed upon as a useful addition.
- [ ] Write user guides


# Documentation

will be soon - user guides will be added when project will be created

# Links
- [Sprints](https://your-website.com/docs/sprints) - information about meetings with the customer and meeting reports
- [AI usage](https://your-website.com/docs/ai-usage.md) - how we use AI in this project.