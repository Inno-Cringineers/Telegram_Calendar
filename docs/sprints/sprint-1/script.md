# Sprint 1 Meeting Script

1. **[Interactive prototype](https://www.figma.com/design/LqJOtos5K1Q8AW5yhVRDQR/Untitled?node-id=0-1&p=f&t=tqUJJL7qTA6588Wm-0)**
   - Show Figma prototype
   - Discuss UI/UX flow

2. **[Strategic plan](../../plan.md)**
   - Present project goals
   - Review threshold of success
   - Discuss feature roadmap

3. **Assumptions**
   - Single user usage of system

4. **Requirements**
   - Discuss [quality requirements](../../requirements/quality-requirements.md)
   - Discuss [functional requirements](../../requirements/user-stories.md)

5. **Constraints**
   - Discuss technical constraints
   - Discuss time constraints
   - Clarify MVP scope

6. **[Initial high-level architecture](../../architecture/architecture.md)**
   - Present architecture diagrams
   - Discuss component responsibilities

## Questions for customer

1. Do we have one user for the system or can there be multiple users for one instance of the system? for example, have I hosted and can I use the bot with someone else or just me? in other words, the system supports multiple users within a single instance, or each user must independently self-host the system for use?

2. Do I need to insert a password into the bot at startup or specify my password during hosting? if the system supports multiple users within the same instance, then it is simply linked to the user's ID and no passwords or IDs are needed for hosting?

3. The event search should be implemented through an interactive calendar or a substring search (event name) - the first is a priority, the second if there are forces?

4. Is it possible to switch notifications to events? for example, to have an event in the external calendar that we linked, but notifications about it did not arrive in the bot, make the ignore and unignore buttons at the event?