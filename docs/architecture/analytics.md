### Value

The **value** for the user is: "All my calendars synced in Telegram bot: I don’t miss meetings and can view and manage my schedule in one place."

### Value moment

The main **value moment** - Get on-time reminder from synced calendar

## Metrics and North Star Metric (NSM)

### Candidate metrics

1. **Bot response time**
Time from user command to bot reply
2. **Number of imported calendars**
Number of calendars user has imported 
3. **Synced external events**
Number of events in the database that come from external calendars (via URL or file).
4. **On-time reminders rate**
Share of reminders that are sent in the expected offset window before event start (±1 minutes from configured offset).

### North Star Metric (NSM)

**NSM: “On-time reminders per active day.”**

Explanation:

- **Measures value to the customer**: if reminders are timely, users can effectively organize their day and avoid missing events.
- **Represents core product strategy**: our primary promise is delivering reliable personal reminders within Telegram - not merely storing calendar events.
- **Leading indicator**: users who receive many on-time reminders are more likely to continue using the bot (higher retention, potential for future self‑hosted use).
- **Actionable now**: If users get fewer timely reminders, they'll stop trusting the bot. We can immediately fix this by adjusting notification times, fixing sync issues, or prompting them to update settings.

### Counter metric

**Counter metric: “Reminders sent too late.”**
Number of reminders that arrive more than 1 minute delay;

### Metric tree

![Metric Tree](/images/metric_tree.png)

## Plan measurements

### Data needed

To calculate the metrics above, we need at least:

**For User activity**

- Event Id
- Date of the Event

**For Reminder quality**

- Scheduled delivery time
- Actual delivery timestamp

**For Number of events**

- Event source (created/imported)
- Event ID

### How much data

Because the bot is single-user per instance and may have low real traffic, we plan to:

- collect data for at least 1-2 **weeks** of synthetic test traffic (team uses the bot, creates events, imports calendars), *this is enough to see stable patterns in reminder timing;*

### How are you going to collect and process this data? Explain and provide a diagram of the pipeline.

we will collect data from logs and databases.

![Pipeline diagram](/images/pipeline_diagram.png)

## Plan code changes

### How should you change your code so that you can collect this data

We don't need to change our code because we already have logs in our system.