# SC&SS JNU Alumni Meet — Database Design

## 1. Purpose

This document defines the initial database model for the School of Computer and Systems Sciences (SC&SS), Jawaharlal Nehru University (JNU), Alumni Meet platform.

The first version of the platform will primarily support:

- Maintaining an alumni database
- Recording Alumni Meet attendance information
- Tracking contributions and payment verification
- Recording dietary requirements and suggestions
- Managing public recognition preferences
- Managing volunteers separately from alumni
- Managing organizer activities and tasks
- Providing a foundation for future invitations and communication features

The current Google Form is an **input/collection mechanism**, not the source of the application's data model. Its columns may change without requiring the underlying database architecture to change.

---

## 2. Core Design Principles

### 2.1 Alumni and volunteers are separate entities

An alumnus is not automatically a volunteer.

The system must **not assume that a volunteer is an alumnus**. A volunteer may be any person helping organize the meet.

Therefore:

- `alumni` stores alumni records.
- `volunteers` stores organizer/volunteer records.
- There is intentionally no foreign-key relationship between the two.

### 2.2 Event-specific information must not be stored permanently in the alumni profile

Information such as:

- attending the current Alumni Meet
- number of accompanying guests
- dietary requirements for the meet
- suggestions for the meet

belongs to a particular meet, not permanently to an alumnus.

Therefore, this information belongs in `meet_responses`.

### 2.3 Contributions are separate records

An alumnus may potentially make more than one contribution.

Therefore, contribution data must not be stored as columns such as `contribution_amount` directly inside `alumni`.

Each contribution should be an independent record linked to:

- the alumnus
- the meet
- the payment information

### 2.4 Payment status must be controlled by the system

A submitted transaction reference or screenshot does not automatically mean that a payment is verified.

The system should distinguish between:

- submitted
- under verification
- verified
- rejected
- refunded

### 2.5 Public visibility must be explicit

Private information such as:

- email
- phone number
- payment details
- payment screenshots

must never become publicly visible merely because an alumnus opted for public recognition.

Public recognition should be stored as a separate preference.

### 2.6 Design for multiple future meets

Although the immediate requirement is the current Alumni Meet, the database should support future meets without redesigning the schema.

---

# 3. High-Level Entity Model

```text
                         ┌──────────────┐
                         │    ALUMNI    │
                         └──────┬───────┘
                                │
                  ┌─────────────┼─────────────┐
                  │             │             │
                  ▼             ▼             ▼
          ┌──────────────┐ ┌───────────┐ ┌─────────────────┐
          │ MEET         │ │           │ │ PUBLIC          │
          │ RESPONSE     │ │           │ │ RECOGNITION     │
          └──────┬───────┘ │           │ └─────────────────┘
                 │         │           │
                 ▼         ▼           │
          ┌──────────────┐             │
          │    MEET      │◄────────────┘
          └──────┬───────┘
                 │
                 ▼
          ┌──────────────┐
          │ CONTRIBUTION │
          └──────────────┘


          ┌──────────────┐
          │  VOLUNTEERS  │
          └──────┬───────┘
                 │
                 ▼
          ┌──────────────┐
          │ ASSIGNMENTS  │
          └──────┬───────┘
                 │
                 ▼
          ┌──────────────┐
          │ ACTIVITIES / │
          │    TASKS     │
          └──────────────┘


          ┌──────────────┐
          │ INVITATIONS  │
          └──────┬───────┘
                 │
                 ▼
               ALUMNI
```

---

# 4. Tables

## 4.1 `alumni`

Stores the relatively stable identity and professional information of an alumnus.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | BIGINT | No | Primary key |
| `full_name` | VARCHAR(200) | No | Full name |
| `graduation_year` | SMALLINT | Yes | Year of graduation |
| `course` | VARCHAR(100) | Yes | Course/program completed |
| `email` | VARCHAR(255) | No | Primary email address |
| `phone` | VARCHAR(30) | Yes | Contact/WhatsApp number |
| `organization` | VARCHAR(255) | Yes | Current organization/company |
| `designation` | VARCHAR(255) | Yes | Current designation/position |
| `current_location` | VARCHAR(255) | Yes | Current city/location |
| `created_at` | DATETIME | No | Record creation time |
| `updated_at` | DATETIME | No | Last modification time |

### Notes

The Google Form currently contains both `Email Address` and `Email ID`.

These should **not** automatically become two database fields.

If they represent the same information, the application should maintain only:

```text
email
```

The original Google Form column `Timestamp` is not required as alumni data. If the original submission timestamp is needed for auditing/import purposes, it should be retained separately in an import/audit mechanism.

### Recommended indexes

```text
PRIMARY KEY (id)
UNIQUE KEY (email)
INDEX (graduation_year)
INDEX (course)
```

Email uniqueness should be confirmed against the actual requirements before enforcing it, because the same email could theoretically be associated with more than one historical record.

---

# 5. `meets`

Represents an Alumni Meet or other alumni-facing gathering.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | BIGINT | No | Primary key |
| `name` | VARCHAR(255) | No | Meet name |
| `description` | TEXT | Yes | Description |
| `event_date` | DATETIME | Yes | Date/time of the meet |
| `venue` | VARCHAR(500) | Yes | Physical/online venue |
| `status` | VARCHAR(30) | No | Planning/live/completed/cancelled |
| `created_at` | DATETIME | No | Creation time |
| `updated_at` | DATETIME | No | Last modification time |

Example:

```text
id: 1
name: SC&SS JNU Alumni Meet 2026
event_date: ...
venue: ...
status: planning
```

### Status values

Recommended application-level values:

```text
planning
registration_open
registration_closed
completed
cancelled
```

---

# 6. `meet_responses`

Stores an alumnus's response for a specific Alumni Meet.

This is the database representation of the event-specific portion of the Google Form.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | BIGINT | No | Primary key |
| `meet_id` | BIGINT | No | FK → `meets.id` |
| `alumni_id` | BIGINT | No | FK → `alumni.id` |
| `attending` | BOOLEAN | No | Whether the alumnus will attend |
| `guest_count` | INT | No | Number of accompanying people excluding the alumnus |
| `total_attendees` | INT | No | Total attendees including alumnus |
| `dietary_preferences` | TEXT | Yes | Dietary preferences/restrictions |
| `suggestions` | TEXT | Yes | Suggestions or activities |
| `submitted_at` | DATETIME | No | Response submission time |
| `updated_at` | DATETIME | No | Last update |

### Important distinction

The form currently asks:

> Total Number of Attendees (Including yourself)

The database should preferably store both:

```text
guest_count
total_attendees
```

However, the application should derive one from the other where appropriate rather than allowing contradictory values.

For example:

```text
guest_count = total_attendees - 1
```

If the form only collects total attendees, `guest_count` can be derived instead of stored.

### Constraint

An alumnus should normally have only one active response per meet:

```text
UNIQUE (meet_id, alumni_id)
```

Updates should modify the existing response rather than create duplicates.

---

# 7. `contributions`

Stores financial contributions made toward a particular Alumni Meet.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | BIGINT | No | Primary key |
| `meet_id` | BIGINT | No | FK → `meets.id` |
| `alumni_id` | BIGINT | No | FK → `alumni.id` |
| `amount` | DECIMAL(12,2) | No | Contribution amount |
| `currency` | CHAR(3) | No | Currency code, e.g. INR |
| `transaction_reference` | VARCHAR(255) | Yes | UTR/payment reference |
| `payment_screenshot_path` | VARCHAR(1000) | Yes | Private storage reference |
| `payment_status` | VARCHAR(30) | No | Payment verification state |
| `submitted_at` | DATETIME | No | Submission time |
| `paid_at` | DATETIME | Yes | Payment time if known |
| `verified_at` | DATETIME | Yes | Verification time |
| `verified_by` | BIGINT | Yes | FK → admin/user, if admin users are implemented |
| `notes` | TEXT | Yes | Internal admin notes |
| `created_at` | DATETIME | No | Creation time |
| `updated_at` | DATETIME | No | Last modification time |

### Recommended payment statuses

```text
submitted
under_review
verified
rejected
refunded
```

### Important

Do **not** store the UPI QR code itself in each contribution.

The QR/UPI destination is configuration for the meet or payment system, not a property of an individual payment.

For example, future design could have:

```text
meet_payment_settings
```

containing:

```text
upi_id
upi_display_name
payment_instructions
```

The current Google Form column:

```text
QR code for Fund collection:
UPI ID:
```

should therefore not become a contribution-table column.

---

# 8. `recognition_preferences`

Controls how an alumnus's contribution or participation may be recognized publicly.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | BIGINT | No | Primary key |
| `meet_id` | BIGINT | No | FK → `meets.id` |
| `alumni_id` | BIGINT | No | FK → `alumni.id` |
| `recognition_type` | VARCHAR(50) | No | Selected public recognition option |
| `created_at` | DATETIME | No | Creation time |
| `updated_at` | DATETIME | No | Last modification |

Possible values might be:

```text
name_only
name_and_batch
name_and_organization
anonymous
```

These values should be finalized based on the exact wording of the final form.

### Why this is separate

Public recognition is not the same as public profile visibility.

For example:

```text
Public website:
Raj Aryan
MCA, 2012
Microsoft
```

does not imply that:

```text
Contribution: ₹10,000
```

should be displayed.

---

# 9. `volunteers`

Volunteers are completely separate from alumni.

A volunteer may be:

- a student
- faculty member
- staff member
- alumnus
- another organizer
- any other person helping with the meet

The database must not require an `alumni_id`.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | BIGINT | No | Primary key |
| `full_name` | VARCHAR(200) | No | Volunteer name |
| `email` | VARCHAR(255) | Yes | Email |
| `phone` | VARCHAR(30) | Yes | Contact number |
| `role` | VARCHAR(100) | Yes | General organizing role |
| `status` | VARCHAR(30) | No | Active/inactive |
| `notes` | TEXT | Yes | Internal notes |
| `created_at` | DATETIME | No | Creation time |
| `updated_at` | DATETIME | No | Last modification |

---

# 10. `activities`

Represents workstreams or activities associated with organizing the meet.

Examples:

```text
Registration Desk
Catering Coordination
Stage Management
Photography
Alumni Communication
Venue Coordination
Welcome Kits
Technical Support
Cultural Program
```

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | BIGINT | No | Primary key |
| `meet_id` | BIGINT | No | FK → `meets.id` |
| `name` | VARCHAR(255) | No | Activity name |
| `description` | TEXT | Yes | Activity details |
| `status` | VARCHAR(30) | No | Activity status |
| `created_at` | DATETIME | No | Creation time |
| `updated_at` | DATETIME | No | Last modification |

Recommended statuses:

```text
planned
in_progress
completed
cancelled
```

---

# 11. `volunteer_assignments`

Connects volunteers to activities/tasks.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | BIGINT | No | Primary key |
| `activity_id` | BIGINT | No | FK → `activities.id` |
| `volunteer_id` | BIGINT | No | FK → `volunteers.id` |
| `responsibility` | TEXT | Yes | What the volunteer is responsible for |
| `status` | VARCHAR(30) | No | Assignment status |
| `created_at` | DATETIME | No | Assignment creation time |
| `updated_at` | DATETIME | No | Last update |

This allows multiple volunteers to work on one activity and one volunteer to participate in multiple activities.

---

# 12. Future `invitations`

Invitations should be designed separately from meet responses.

An invitation represents a communication sent to an alumnus for a particular meet.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `id` | BIGINT | No | Primary key |
| `meet_id` | BIGINT | No | FK → `meets.id` |
| `alumni_id` | BIGINT | No | FK → `alumni.id` |
| `channel` | VARCHAR(30) | No | email/whatsapp/etc. |
| `status` | VARCHAR(30) | No | Invitation status |
| `sent_at` | DATETIME | Yes | Time sent |
| `opened_at` | DATETIME | Yes | Time opened, if supported |
| `responded_at` | DATETIME | Yes | Response time |
| `created_at` | DATETIME | No | Creation time |

Possible statuses:

```text
draft
queued
sent
delivered
opened
failed
```

The invitation system can be implemented later without changing the core alumni/contribution model.

---

# 13. Authentication and Admin Users

Authentication should be kept separate from alumni records.

A future `users` table may contain:

```text
users
─────
id
email
password_hash
role
is_active
created_at
updated_at
```

Possible roles:

```text
admin
organizer
volunteer
```

Do not store plaintext passwords.

If authentication is implemented through an external identity provider, the schema can instead store the provider's user identifier.

---

# 14. Google Form Mapping

Current Google Form columns should map approximately as follows.

| Google Form Column | Database destination |
|---|---|
| Timestamp | Import/audit metadata, not `alumni` |
| Email Address | `alumni.email` |
| Full Name | `alumni.full_name` |
| Graduation Year | `alumni.graduation_year` |
| Course | `alumni.course` |
| Email ID | `alumni.email` if duplicate |
| Contact/Whatsapp Number | `alumni.phone` |
| Current Organization / Company | `alumni.organization` |
| Current Designation / Position | `alumni.designation` |
| Current Location | `alumni.current_location` |
| Will you be attending the Alumni Meet? | `meet_responses.attending` |
| Accompanied by family/friends? | Derived from attendee information or response metadata |
| Total Number of Attendees | `meet_responses.total_attendees` |
| UPI ID / QR code | Meet/payment configuration |
| Payment Transaction ID / UTR | `contributions.transaction_reference` |
| Upload Payment Screenshot | `contributions.payment_screenshot_path` |
| Public Recognition Preference | `recognition_preferences.recognition_type` |
| Dietary Preferences / Restrictions | `meet_responses.dietary_preferences` |
| Suggestions / Activities | `meet_responses.suggestions` |
| Would you like to volunteer? | Not stored as a volunteer relationship |

## Volunteer Form Handling

Because volunteers are independent of alumni, the current question:

```text
Would you like to volunteer or be part of the organizing committee?
```

should **not** directly create an alumnus → volunteer relationship.

If the answer is yes, the system can later:

1. Collect the person's volunteer information.
2. Create a record in `volunteers`.
3. Allow organizers to assign that volunteer to activities.

If the same person happens to also be an alumnus, that can be recorded independently without coupling the two entities.

---

# 15. Privacy Classification

The following classification should be enforced at the application/API level.

## Private

```text
email
phone
payment transaction reference
payment screenshot
payment status
internal admin notes
volunteer contact information
```

## Internal organizer data

```text
dietary restrictions
guest count
attendance information
volunteer assignments
organizer notes
```

## Potentially public

Only when explicitly permitted:

```text
full name
graduation year
course
organization
designation
```

Public recognition settings should control what is displayed.

Never expose payment screenshots or transaction references through public APIs.

---

# 16. Foreign-Key Relationships

Conceptually:

```text
alumni
  │
  ├──────────────< meet_responses >────────────── meets
  │
  ├──────────────< contributions >─────────────── meets
  │
  ├──────────────< recognition_preferences >───── meets
  │
  └──────────────< invitations >────────────────── meets


meets
  │
  └──────────────< activities
                       │
                       └────< volunteer_assignments >──── volunteers
```

---

# 17. Recommended Constraints

At minimum:

```text
alumni.email
    UNIQUE where appropriate

meet_responses
    UNIQUE (meet_id, alumni_id)

recognition_preferences
    UNIQUE (meet_id, alumni_id)

invitations
    INDEX (meet_id, alumni_id)

contributions
    INDEX (meet_id, alumni_id)

volunteer_assignments
    UNIQUE (activity_id, volunteer_id)
```

Foreign keys should use appropriate `ON DELETE` behavior.

For important financial records such as contributions, prefer preventing accidental deletion rather than cascading deletes.

---

# 18. Monetary Data

Never use floating-point types for money.

Use:

```text
DECIMAL(12,2)
```

instead of:

```text
FLOAT
DOUBLE
```

For the current Indian use case:

```text
currency = INR
```

The currency field is retained so the system is not unnecessarily locked to one currency in the future.

---

# 19. Payment Screenshot Storage

Payment screenshots should **not** be stored directly as database BLOBs unless there is a specific reason.

Prefer:

```text
Object/File Storage
        │
        ▼
Private file
        │
        ▼
Database stores file reference/path
```

Example:

```text
payment_screenshot_path
    = private/payments/2026/abc123.png
```

The backend should generate an authorized/private access mechanism when an organizer needs to view the screenshot.

Public users must never be able to guess or directly access payment files.

---

# 20. Auditability

Because this system handles financial information and organizer operations, important actions should eventually be auditable.

A future table can be:

```text
audit_logs
──────────
id
user_id
action
entity_type
entity_id
old_value
new_value
created_at
```

Useful actions include:

```text
CONTRIBUTION_VERIFIED
CONTRIBUTION_REJECTED
CONTRIBUTION_REFUNDED
ALUMNI_UPDATED
VOLUNTEER_CREATED
VOLUNTEER_ASSIGNED
INVITATION_SENT
```

This does not need to be implemented in the first version, but the application should be structured so it can be added later.

---

# 21. Google Form Import Strategy

Since the form currently has **zero submissions**, there is no need to build a complex synchronization system immediately.

Recommended initial workflow:

```text
Google Form
     │
     ▼
Google Sheet
     │
     ▼
Admin import
     │
     ▼
Validation / normalization
     │
     ▼
Database
```

The import process should:

1. Read each response.
2. Normalize names, emails, phone numbers, etc.
3. Find an existing alumnus where appropriate.
4. Create/update the `alumni` record.
5. Create the corresponding `meet_response`.
6. Create contribution data only when valid payment information exists.
7. Store the recognition preference.
8. Handle volunteer interest separately if required.

The database should not depend on the exact order or spelling of Google Form columns.

---

# 22. Future Features Supported by This Design

The schema is intentionally designed to allow future additions such as:

### Invitations

```text
Alumni
  ↓
Invitation
  ↓
Email / WhatsApp
  ↓
Meet response
```

### Contribution dashboard

```text
Total contributions
Verified contributions
Pending verification
Rejected payments
Number of contributors
Average contribution
```

### Alumni directory

```text
Batch
Course
Name
Organization
Designation
Location
```

with privacy controls.

### Volunteer management

```text
Volunteer
  ↓
Activity
  ↓
Assignment
  ↓
Task status
```

### Multiple Alumni Meets

```text
2026 Meet
2027 Meet
2028 Meet
...
```

without duplicating alumni records.

---

# 23. Initial MVP

The first implementation should stay small.

## MVP database

Implement:

```text
alumni
meets
meet_responses
contributions
recognition_preferences
volunteers
```

Add:

```text
activities
volunteer_assignments
```

when organizer workflow begins.

Add later:

```text
invitations
users
audit_logs
meet_payment_settings
```

as those features become necessary.

---

# 24. Recommended First Meet Record

The application should create one meet record for the current event, for example:

```text
SC&SS JNU Alumni Meet 2026
```

All current form responses and contributions should reference this `meet_id`.

This is the key decision that keeps the system reusable.

---

# 25. Summary

The core model is:

```text
                         ┌───────────┐
                         │  ALUMNI   │
                         └─────┬─────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      MEET_RESPONSES     CONTRIBUTIONS    RECOGNITION
             │                 │                 │
             └─────────────────┼─────────────────┘
                               │
                               ▼
                             MEETS


                         ┌────────────┐
                         │ VOLUNTEERS │
                         └──────┬─────┘
                                │
                                ▼
                       VOLUNTEER_ASSIGNMENTS
                                │
                                ▼
                           ACTIVITIES


                         FUTURE
                            │
                            ▼
                       INVITATIONS
```

The most important architectural rule is:

> **Alumni data, meet participation, contributions, and volunteer management are separate concerns.**

The Google Form can evolve independently while the database remains stable.

---

# 26. Documentation Maintenance

`PROJECT_INSTRUCTIONS.md` is the first-read project instruction file.

Whenever the database model or data-related requirements change, update this document.

Examples of changes requiring an update:

- New table/entity
- New column
- Changed relationship
- Changed constraint
- New index
- Changed privacy classification
- Changed Google Form mapping
- Changed contribution/payment data model
- Changed data lifecycle
- New audit or authentication data

If a database change affects application architecture or UI, also update `architecture.md` and/or `design.md`.

Do not leave important database decisions only in chat history.
