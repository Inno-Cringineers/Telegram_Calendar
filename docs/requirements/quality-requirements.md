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
- Reminder delay does not exceed 1 minute.

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
**Stimulus:** Attempt to access the calendar bot from a Telegram account other than the one initially registered
**Environment:** Normal system operation
**Response:** The bot allows full calendar access and interaction only to the Telegram account of the first user who ever contacted it. Any further access attempts from other Telegram accounts will be ignored.
**Response Measure:**
- 100% of attempts by any Telegram account other than the registered user will be ignored.
- The ID of the authorized user is persistently stored

### **QAST003-1: Only First User Access**

**Steps:**  
1. First-time user interaction with bot 
2. Attempt to send a command from a different Telegram account.

**Expected Result:** 
- The second user does not receive any response or access to data.

**Success Criteria:** 
- 100% of unauthorized access attempts are ignored.

### **QAST003-2: Persistent Authorized ID**

**Steps:**  
1. First-time user interaction with bot 
2. Restart the bot.
3. Attempt access from another account.

**Expected Result:** 
- Only the first user can access the bot.

**Success Criteria:** 
- Authorized user ID is retained after a restart.

---

### **QAS004: Import of Large Number of Events**
**Source of Stimulus:** User
**Stimulus:** Importing a calendar with 50 events
**Environment:** Normal system operation
**Response:** The system parses, saves events and generates reminders
**Response Measure:**
- Import time does not exceed 3 minutes per 50 events

### **QAST004-1: Import 50 Events Within Limit**
**Precondition:**
- Prepare a .ics link with 50 events.

**Steps:**  
1. Import it through the bot.
2. Measure total import time.

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
1. Change quiet hours.
2. Create a reminder.

**Expected Result:** 
- The new reminder respects the updated quiet hours.

**Success Criteria:** 
- All new reminders match the new preferences.

---

### **QAS006: Event Update Consistency**
 **Source of Stimulus:** User
 **Stimulus:** Updating an event that has active reminders
 **Environment:** Normal system operation
 **Response:** All related reminders are updated or removed consistently with event changes
 **Response Measure:**
- When an event is modified, all related reminders are updated
- No notifications for non-existent events

### **QAST006-1: Reminders Updated After Event Change**

**Steps:**  
1. Create an event with a reminder.
2. Change the event time.
3. Verify the updated reminder time.

**Expected Result:** 
- Reminder delivery time corresponds to the updated event time
- No reminders are sent based on the previous event timing


### **QAST006-2: No Lost Notifications After Deletion**

**Steps:**  
1. Delete an event with an active reminder.
2. Wait for the original reminder time.

**Expected Result:** 
- No reminder is sent for the deleted event.

**Success Criteria:** 
- No notifications for non-existent events.

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
4. Check that events, reminders, and settings are not changed.

**Expected Result:** 
- All data and reminders are restored; reminders are delivered as scheduled.

**Success Criteria:** 
- 100% data recovery (zero loss of events, reminders, or settings)
- Normal operation resumes within 5 minutes.
--- 

