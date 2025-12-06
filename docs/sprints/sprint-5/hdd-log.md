## HDD log
We selected metric - imported events because Every imported event is a potential reminder -> directly impacts core product value.

Current value this metric is 0 because we not implemented this functional.

### Hypotheses
1. We believe that **implementing ICS calendar import functionality** for **our Telegram bot users** will result in **successful import of external calendar events** when **users provide valid ICS file URLs** because **ICS is a universal calendar format supported by all major calendar providers.**
2. We believe that **hourly ICS synchronization** for **active calendar users** will result in **increasing imported events** when **users have dynamic schedules** because **current daily sync misses events added between synchronization windows, reducing the number of imported events available for reminders.**
3. We believe that **implementing OAuth authentication with Google, Outlook, and Apple calendars** for **our Telegram bot users** will result in **increased number of imported events** when **users authorize access** because **major calendar providers offer comprehensive APIs that expose complete event data, enabling our system to access structured schedule information without requiring users to manually export or transfer calendar data.**

We chose the first hypothesis because without ICS import, nothing else works. No calendar data -> no reminders -> no product value.

![External events count](/images/external_events_count.png)

In screenshot we can see that we import calendar and new external events added.

### How many real users (if you had them) would be enough for this experiment?

One user would be enough.

### How much data would be enough?

We need an ics link to the event calendar.