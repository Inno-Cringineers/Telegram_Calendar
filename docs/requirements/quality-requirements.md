# Quality Requirements

## Table of contents

- [Priority matrix](#priority-matrix)
- [QAS priority rationale](#quality-attribute-scenario-priority-rationale)
- [Quality attribute scenarios](#quality-attribute-scenarios)

## Priority matrix

Business Importance →
Technical risk ↓ | L | M | H
---|---|---|---
L | 003 | 001|006
M | |005 |002
H | | |007, 004

L - low, M - medium, H - high


## Quality Attribute Scenario Priority Rationale

### High Business Priority Scenarios
- Core product value (QAS002, QAS004)
- Critical for self-hosted reliability (QAS007)
- Foundation of user trust(QAS6)

### High Technical Priority Scenarios

- External calendar API integration(QAS004)
- Complex system health recovery(QAS007)


### Medium Business Priority Scenarios

- Additional customization features (QAS005)
- Enhanced user satisfaction through faster responses(QAS001)

### Medium Technical Priority Scenarios

- Performance optimization(QAS001)
- Typical preference storage mechanisms (QAS005)

### Low Business Priority Scenarios

- Minimal impact on core functionality (QAS003)

### Low Technical Priority Scenarios

- Minimal technical complexity(QAS001, QAS003, QAS006)


## Quality attribute Scenarios


### **QAS001: Command Response Time**
  **Source of Stimulus**: User
  **Stimulus**: User sends a bot command
  **Environment:** Normal system operation 
  **Artifact:** Telegram bot processing pipeline.
  **Response:** System processes the command and replies to the user with the result
  **Response Measure:**
- 98% of commands respond within 5 seconds

### **QAST001-1: Fast Response for Typical Command**

**Steps:**  
1. Send the command to the Telegram bot. 
2. Measure the time between sending the command and receiving the response. 

**Expected Result:** 
- The bot replies within 5 seconds. 

**Success Criteria:** 
- At least 49 out of 50 attempts respond in 5 seconds or less.
---

### **QAS002: Reliable Reminder Scheduling**
 **Source of Stimulus:** User
 **Stimulus:** create events with reminders
 **Environment:** Normal system operation
 **Artifact:** Reminder Scheduler
 **Response:** System schedules and delivers reminders accurately
 **Response Measure:**
- Maximum reminder delay does not exceed 1 minute
- Zero reminder loss or duplication

### **QAST002-1: Reminder Delivered on Time**

**Steps:**  
1. Create an event with a reminder set for 1 minute before the event. 
2. Wait for the reminder to be delivered.

**Expected Result:**  
- Reminder is delivered no more than 1 minute after their scheduled time

**Success Criteria:** 
- 5/5 test reminders delivered within 1 minute of scheduled time

### **QAST002-2: No Loss or Duplication**

**Steps:**  
1. Create 5 events with reminders.
2. Check that each reminder is delivered exactly once.

**Expected Result:** 
- Each reminder appears only once; none are missed.

**Success Criteria:** 
- 0 missed reminders, 0 duplicates in a set of 5.

---

### **QAS003: User Data Confidentiality**
**Source of Stimulus:** User
**Stimulus:** Attempt to access the calendar bot from a Telegram account other than the primary
**Environment:** Normal system operation
**Response:** The bot allows full calendar access and interaction only to the Telegram account of the first user who ever contacted it. Any further access attempts from other Telegram accounts will be ignored.
**Response Measure:**
- 100% of attempts by any Telegram account other than the primary user will be ignored.
- The ID of the primary user is persistently stored

### **QAST003-1: Only First User Access**
**Preconditions**
- User already interact with bot

**Steps:**  
1. Send a command to the bot from 5 different Telegram accounts.

**Expected Result:** 
- Users does not receive any response or access to data.

**Success Criteria:** 
- 100% of commands from non-primary users are ignored


---

### **QAS004: Import calendar**
**Source of Stimulus:** User
**Stimulus:** Importing a calendar events via ics link
**Environment:** Normal system operation
**Response:** The system parses, saves events and generates reminders
**Response Measure:**
- Import time does not exceed 3 minutes.

### **QAST004-1: Import calendar with 50 Events **
**Precondition:**
- Prepare a ics links with 50 events.

**Steps:**  
1. Send ics links to the bot.

**Expected Result:** 
- Import completes within 3 minutes.

**Success Criteria:** 
- All 50 events imported with no duplicates or errors.

---

### **QAS005: Persistent User Preferences**
**Source of Stimulus:** User
**Stimulus:** The user sets their preferences (timezone, language, quiet hours)
**Environment:** Normal system operation
**Response:** Preferences are saved instantly and reliably; changes are applied to new reminders
**Response Measure:**
- 100% of preference changes persist
- Changes are applied to all new reminders within 1 minute

### **QAST005-1: Preference Affects Reminders**

**Steps:**  
1. Set quiet hours to start in 3 minutes, duration = 5 minutes.
2. Create an event in 5 minutes with 1-minute reminder

**Expected Result:** 
- The reminder is not sent.

**Success Criteria:** 
- All reminders match the new preferences.

### QAST005-2: Event During Quiet Hours - Reminder Before

**Steps:**  
1. Set quiet hours: NOW+3 minutes to NOW + 25 minutes
2. Create event at NOW+10 minutes (during quiet hours) with 5-minutes reminder

**Expected Result:** 
- No reminder is sent after 5 minutes (original reminder time during quiet hours)
- Reminder is sent at 3 minutes (immediately before quiet hours start)

**Success Criteria:** 
- Zero notifications sent during active quiet hours period

### QAST005-3: Event After Quiet Hours - Reminder During

**Steps:**  
1. Set quiet hours: NOW + 2 minutes to NOW + 20 minutes
2. Create event at NOW + 25 minutes (after quiet hours) with 10-minute reminder

**Expected Result:** 
- Reminder is sent at NOW + 20 minutes (after quiet hours)
- No reminder at NOW + 15 minutes (original reminder time during quiet hours) 

**Success Criteria:** 
- 100% of reminders that fall during quiet hours are rescheduled to end quiet hours

---

### **QAS006: Event Update Consistency**
 **Source of Stimulus:** User
 **Stimulus:** Updating an event that has reminders
 **Environment:** Normal system operation
 **Response:** All related reminders are rescheduled or removed consistently with event changes
 **Response Measure:**
- All related reminders are rescheduled according to event changes

### **QAST006-1: Reminders Updated After Event Change**

**Steps:**  
1. Create an event in 5 minutes with 3-minute reminder
2. Сhange the time of the event in 7 minutes

**Expected Result:** 
- Reminder is delivered in 4 minutes (3 minutes before new event time)
- No reminder is delivered in 2 minutes (original reminder time)

**Success Criteria:** 
- 0/5 reminders are delivered depending on the previous time of the event.
- 5/5 reminders are delivered depending on the new time of the event.

### **QAST006-2: No Lost Notifications After Deletion**

**Steps:**  
1. Create 5 events with reminders
2. Delete 3 random events

**Expected Result:** 
- 0/3 reminders delivered for deleted events
- 2/2 reminders delivered for remaining events

**Success Criteria:** 
- 0% false positives in reminder cancellation

---

### **QAS007: Fault Tolerance and Recovery**
**Source of Stimulus:** System failure, process crash, or server reboot
**Stimulus:** Unexpected bot or persistence layer failure during operation
**Environment:** Production deployment
**Response:** The system automatically restores scheduled reminders, calendar events, user preferences, and authorization state after restart. Users do not experience data loss.
**Response Measure:**
- Zero loss of reminders, events, or user settings after recovery
- System resumes normal operation within 5 minutes of failure

### **QAST007-1: Recovery After Crash**

**Steps:**  
1. Create an event and schedule a reminder.
2. Simulate a crash (kill the bot process).
3. Restart the bot.

**Expected Result:** 
- All data and reminders are restored; reminders are delivered as scheduled.

**Success Criteria:** 
- 100% data recovery (zero loss of events, reminders, or settings)
- Normal operation resumes within 5 minutes.
--- 

