# Plan

## Project goals

Provide to users a tool to create their own planning service (self hosted). Which will Combine notifications from multiple calendars in one place (telegram bot) and provide the opportunity to perform CRUD operations with events and receive reminders centralized from all provided calendars and events.

MVP features have to be done before ITPD Course finish (19.12.2025)

## Threshold of Success

1. **MVP Delivery**: By the end of the course, deliver a working Telegram Calendar bot with all critical MVP features passing acceptance tests with no critical bugs.

2. **Self-hosting**: By the end of the course, at least one test user successfully self-host the application using our Docker setup within 40 minutes, with no assistance beyond the provided documentation.

3. **Quality & Performance**: All implemented core MVP features meet QAS and tested by the end of the course.

4. **Passing a course**: All team members passed a course by the end.

## Feature roadmap

Key Features Identified:

- F1 Reminders with configurable number of time before an event.
- F2 Time zones support (manual user setting).
- F3 A "Daily Plan" feature - a summary of the day's events sent at a user-defined time.
- F4 Integration with calendars via standardized iCal (ICS) format files / links.
- F5 Ability to add, edit, and delete events directly within the bot (these events will be stored internally in the bot, not synced to external calendars).
- F6 Users must be able to import/export their internally-created events in ICS format, for backup or transfer.
- F7 Event Viewing: Users will be able to view all events by selected days.
- F8 Quiet Hours: A "Do Not Disturb" feature to mute notifications during specific hours was agreed upon as a useful addition.
- F9 Russian and English languagues support.
- F10 Selfhosting app with easly deployment by docker
- F11 Personal user access to bot (one instance for one user)
- F12 Repeated events support

## Progress monitoring

- Sprints & Meetings
	- Weekly sprint (1-week sprint) with a Sprint Planning, Meeting with customer, Review.
	- Four short async status updates per week in the project Telegram group: (1) in progress, (2) pending, (3) blockers, (4) done.
	- Ad-hoc technical syncs when a critical blocker appears.

- Artifacts & tooling
	- Work tracked via GitHub Issues and GitHub Projects (Board + Roadmap). Every feature or bug must have an issue with acceptance criteria.
	- Pull requests must reference the issue they implement.

- Metrics to watch (minimum viable set)
	- Sprint progress: story points (or task count) completed vs. planned per sprint.
	- Open defects: number of open bugs.

## Contingency plans

1) Schedule slip (we're behind plan)
	 - Trigger: sprint whas completed story points < 70% of planned.
	 - Immediate actions:
		 - Perform re-prioritization: move lower-value or non-core features to a post-MVP backlog.
		 - Freeze UI/UX polish and non-essential tasks; focus on core features.

2) Technical blocker
	 - Trigger: core feature fails and blocks the MVP flow.
	 - Immediate actions:
		 - Implement a fallback: accept raw implementation of feature / fallback feature.

3) Quality regression (too many bugs)
	 - Trigger: more than 5 open high/medium bugs affecting core flows.
	 - Immediate actions:
		 - Halt new feature merges; create a stabilization sprint focused on fixing bugs and raising test coverage for core flows.

4) Requirements change
	 - Trigger: new requirements request that affects core scope or timeline.
	 - Immediate actions:
		 - Evaluate the request's business value and technical risk quickly.
		 - Set customer expectations to realistic resources.
