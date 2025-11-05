# Quality Requirements

## Table of contents

- [Priority matrix](#priority-matrix)
- [Quality attribute scenarios](#quality-attribute-scenarios)

## Priority matrix

Business Importance →
Technical risk ↓ | L | M | H
---|---|---|---
L | | |
M | | |
H | | |

L - low, M - medium, H - high

## <Quality attribute> Scenarios


### **QAS001: Command Response Time**
  **Source of Stimulus**: User
  **Stimulus**: User sends a bot command
  **Environment:** Normal system operation 
  **Artifact:** Telegram bot processing pipeline.
  **Response:** System processes the command and replies to the user with the result
  **Response Measure:**
- 99% of commands respond within 5 seconds

### **QAS002: Reliable Reminder Scheduling**
 **Source of Stimulus:** User
 **Stimulus:** create events with reminders
 **Environment:** Normal system operation
 **Artifact:** Reminder Scheduler
 **Response:** System schedules and delivers reminders accurately
 **Response Measure:**
- Maximum reminder delay does not exceed 1 minute
- Zero reminder loss or duplication

### **QAS003: User Data Confidentiality**
**Source of Stimulus:** User
**Stimulus:** Attempt to access the calendar bot from a Telegram account other than the one initially registered
**Environment:** Normal system operation
**Response:** The bot allows full calendar access and interaction only to the Telegram account of the first user who ever contacted it. Any further access attempts from other Telegram accounts will be ignored.
**Response Measure:**
- 100% of attempts by any Telegram account other than the registered user will be ignored.
- The ID of the authorized user is persistently stored

### **QAS004: Import of Large Number of Events**
**Source of Stimulus:** User
**Stimulus:** Importing a calendar with 50 events
**Environment:** Normal system operation
**Response:** The system parses, saves events and generates reminders
**Response Measure:**
- Import time does not exceed 3 minutes per 50 events

### **QAS005: Persistent User Preferences**
**Source of Stimulus:** User
**Stimulus:** The user sets their preferences (timezone, language, quiet hours)
**Environment:** Normal system operation
**Response:** Preferences are saved instantly and reliably; changes are applied to new reminders
**Response Measure:**
- 100% of preference changes persist
- Changes are applied to all new reminders within 1 minute

### **QAS006: Event Update Consistency**
 **Source of Stimulus:** User
 **Stimulus:** Updating an event that has active reminders
 **Environment:** Normal system operation
 **Response:** All related reminders are updated or removed consistently with event changes
 **Response Measure:**
- When an event is modified, all related reminders are updated
- No notifications for non-existent events

### **QAS007: Fault Tolerance and Recovery**
**Source of Stimulus:** System failure, process crash, or server reboot
**Stimulus:** Unexpected bot or persistence layer failure during operation
**Environment:** Production deployment
**Response:** The system automatically restores scheduled reminders, calendar events, user preferences, and authorization state after restart. Users do not experience data loss.
**Response Measure:**
- Zero loss of reminders, events, or user settings after recovery
- System resumes normal operation within 5 minutes of failure

### QAST001-1

**Test description:** 
**Expected result:** 

