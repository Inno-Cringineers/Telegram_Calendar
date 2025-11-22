# Meeting date.

meeting started at 21.11.2025 18:03

meeting ended at 21.11.2025 18:24

# Link to the playable recording with sound.

playable recording with sound (meeting_4_at_20251121_180300.m4a) available via the link:

https://drive.google.com/drive/folders/1lFrmgIr-B6MBpstlfxNTnKZliYNLUD5s?usp=drive_link

# Action points

## UI/UX Design

**WHAT:** Implement a health check and monitoring system for the bot.
   **WHO:** 
   **WHEN:**  sprint

**WHAT:** Investigate and implement a method to track message delivery latency (time from receiving a user message to sending a response).
   **WHO:** 
   **WHEN:**  sprint
  

**WHAT:** Add the 'single-user-restriction' configuration flag to the bot's setup (via .env or config file).
   **WHO:** 
   **WHEN:**  sprint

**WHAT:** Update the project's README with clear, step-by-step instructions for running the bot via Docker Compose.
   **WHO:** 
   **WHEN:**  sprint

**WHAT:** Discuss and define a strategy for tracking bot usage
   **WHO:** 
   **WHEN:**  sprint
   

# Summary of the meeting.
The client has approved the core prototype, and we have successfully concluded an exploratory sprint that established the project's foundation. To date, we have completed the localization of the interface into Russian, set up the infrastructure including tests, linters, and a CI/CD pipeline via GitHub Actions, and developed the core Data Models. This last milestone unblocks the implementation of the business logic.

In the immediate future, we will introduce a flexible configuration system using a SINGLE_USER_RESTRICTION parameter in the .env file. This will allow switching between a single-user mode and a multi-user mode. Deployment will be simplified using Docker Compose, and the README.md will be updated with corresponding setup instructions.

To ensure reliability, we are developing a monitoring system that includes a /health endpoint and a separate service for failure notifications. We are also implementing logging for request processing times to track performance. Key technical decisions include prioritizing user confidentiality by avoiding centralized log collection and acknowledging the limitations of the Telegram API regarding message delivery tracking.



# List of speakers. (Github usernames).

- **Customer** - [deemp](https://github.com/deemp)
- **Main Speaker** - [rikire](https://github.com/rikire)
- **Secondary Speakers**:
  - [Ten-Do](https://github.com/Ten-Do)
  - [03sano30](https://github.com/03sano30)
  - [abdra04-gif](https://github.com/abdra04-gif)

  # Transcript of the recording with timestamps and speaker labels.

Transcript of the recording with timestamps and speaker labels (./meeting_х_Transcript/"meeting_4_at_20251121_180300_speaker_en_bilingual_timestamps.txt") available via the link:

https://drive.google.com/drive/folders/1lFrmgIr-B6MBpstlfxNTnKZliYNLUD5s?usp=drive_link