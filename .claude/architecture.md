# SC&SS JNU Alumni Meet Platform — System Architecture

## 1. Overview

The SC&SS JNU Alumni Meet Platform is a web application for managing alumni information, Alumni Meet participation, contributions, payment verification, volunteers, organizer activities, and eventually invitations and communication.

The system is intentionally designed so that:

- Alumni and volunteers are separate concepts.
- The Google Form is an input/collection source, not the application's permanent data model.
- TiDB is the only application database.
- No MySQL server is used.
- No ORM is used.
- Payment screenshots are stored in Google Drive, while TiDB stores a reference to the file.
- The initial implementation can remain small while providing a clean path to future features.

The database model defined here is based on the current database design. fileciteturn0file0L5-L18

---

# 2. Technology Stack

## Frontend

```text
HTML
CSS
Vanilla JavaScript
Jinja2 templates
```

No frontend framework is required for the initial version.

The frontend communicates with Flask through:

1. Server-rendered HTML/Jinja2 for normal pages.
2. JSON endpoints where asynchronous interactions are useful.

---

## Backend

```text
Python
Flask
```

Responsibilities:

- Routing
- Request handling
- Authentication and authorization
- Server-side validation
- Business rules
- Database access
- Google Drive integration
- Google Sheets/Form import
- Future invitation/communication integrations
- Rendering Jinja2 templates
- Returning JSON responses where required

---

## Database

```text
TiDB
```

The application uses TiDB directly through its MySQL-compatible protocol.

Important constraints:

```text
No MySQL server
No SQLite fallback
No ORM
No SQLAlchemy
```

Database interaction should use a Python TiDB/MySQL-compatible driver and parameterized SQL queries.

---

## File Storage

```text
Google Drive
```

Google Drive is the storage location for payment screenshots.

TiDB stores only metadata/reference information such as:

```text
payment_screenshot_file_id
```

The image itself is not stored inside TiDB.

---

## Source / Import System

```text
Google Form
      ↓
Google Sheet
      ↓
Flask import/processing layer
      ↓
TiDB
```

The current form has no submissions, so the first implementation does not need continuous synchronization.

---

# 3. High-Level Architecture

```text
                         ┌───────────────────────────┐
                         │          USERS            │
                         │                           │
                         │ Alumni | Organizers       │
                         │ Volunteers | Admins       │
                         └─────────────┬─────────────┘
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │       WEB BROWSER         │
                         │                           │
                         │ HTML / CSS / JavaScript   │
                         └─────────────┬─────────────┘
                                       │
                              HTTP / HTTPS
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FLASK APPLICATION                        │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐  │
│  │ Public Routes│   │ Admin Routes │   │ Future API Routes  │  │
│  └───────┬──────┘   └──────┬───────┘   └─────────┬──────────┘  │
│          │                   │                     │             │
│          └───────────────────┼─────────────────────┘             │
│                              ▼                                   │
│                    ┌──────────────────┐                          │
│                    │ Business /       │                          │
│                    │ Service Layer    │                          │
│                    └────────┬─────────┘                          │
│                             │                                    │
│                ┌────────────┼─────────────┐                     │
│                ▼            ▼             ▼                     │
│        ┌─────────────┐ ┌──────────┐ ┌──────────────┐           │
│        │ TiDB Access │ │ Google   │ │ Auth /       │           │
│        │ Layer       │ │ Drive    │ │ Security     │           │
│        └──────┬──────┘ │ Service  │ └──────────────┘           │
│               │        └────┬─────┘                             │
└───────────────┼─────────────┼──────────────────────────────────┘
                │             │
                ▼             ▼
          ┌───────────┐  ┌─────────────┐
          │   TiDB    │  │ Google Drive│
          │ Database  │  │ File Storage│
          └───────────┘  └─────────────┘
```

---

# 4. Major System Components

## 4.1 Public Website

The public website is the presentation layer for alumni and visitors.

Potential pages:

```text
/
├── Home
├── About
├── Alumni Meet
├── Contribute
├── Alumni
├── Gallery
└── Contact
```

The initial version does not need all of these.

The first release can focus on:

```text
Home
Alumni Meet
Contribute
```

---

# 5. Admin / Organizer Application

The organizer dashboard is separate from the public-facing website.

```text
/admin
```

Potential modules:

```text
Dashboard
├── Alumni
├── Meet
├── Contributions
├── Payment Verification
├── Volunteers
├── Activities
├── Invitations
└── Settings
```

The dashboard should be protected by authentication and authorization.

---

# 6. Application Layers

The Flask application should be organized into logical layers.

```text
Browser
   │
   ▼
Routes / Controllers
   │
   ▼
Services / Business Logic
   │
   ├──────────────► Database Access
   │
   ├──────────────► Google Drive
   │
   └──────────────► Google Sheets / Form Import
```

## Routes

Routes should deal primarily with:

- HTTP requests
- URL parameters
- authentication checks
- input extraction
- response generation

Routes should not contain large amounts of business logic or SQL.

Example:

```text
GET  /admin/contributions
POST /admin/contributions/<id>/verify
GET  /alumni
GET  /meet
```

---

## Services

Services contain application/business logic.

Example:

```text
alumni_service
contribution_service
meet_service
volunteer_service
import_service
drive_service
invitation_service
```

Example responsibility:

```text
contribution_service.verify_contribution()
```

The route calls the service.

The service:

1. Validates the request.
2. Checks contribution state.
3. Updates TiDB.
4. Records verification information.
5. Returns the result.

---

# 7. Database Access

Because no ORM is being used, all SQL should be explicit.

Recommended flow:

```text
Route
  ↓
Service
  ↓
Repository / DB function
  ↓
Parameterized SQL
  ↓
TiDB
```

Example conceptual structure:

```text
db/
├── connection.py
├── alumni.py
├── meets.py
├── meet_responses.py
├── contributions.py
├── volunteers.py
└── activities.py
```

The DB layer should:

- Create/reuse connections safely.
- Execute parameterized queries.
- Commit transactions explicitly.
- Roll back failed transactions.
- Close/release connections correctly.
- Never construct SQL using user-provided string concatenation.

---

# 8. Core Data Architecture

The database is centered around the following concepts:

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

The database separates alumni profile information from meet-specific information and contributions. fileciteturn0file0L22-L88

---

# 9. Alumni Domain

## `alumni`

Stores stable alumni information:

```text
id
full_name
graduation_year
course
email
phone
organization
designation
current_location
created_at
updated_at
```

The Google Form's `Email Address` and `Email ID` should not automatically become separate database fields if they represent the same email. fileciteturn0file0L146-L187

### Data flow

```text
Google Form / Future Website
            │
            ▼
      Validation
            │
            ▼
        Alumni Service
            │
            ▼
           TiDB
            │
            ▼
         `alumni`
```

---

# 10. Alumni Meet Domain

## `meets`

Represents the Alumni Meet itself.

For the current project, the initial record will represent:

```text
SC&SS JNU Alumni Meet 2026
```

The schema intentionally allows future meets:

```text
SC&SS JNU Alumni Meet 2026
SC&SS JNU Alumni Meet 2027
SC&SS JNU Alumni Meet 2028
...
```

This prevents duplicate alumni records across different meets.

---

## `meet_responses`

Stores information specific to an alumnus's participation in a particular meet.

```text
alumni
   │
   ▼
meet_responses
   │
   └── meet
```

Information includes:

```text
attending
guest_count / total_attendees
dietary_preferences
suggestions
```

This keeps event-specific information out of the permanent alumni profile. fileciteturn0file0L36-L47

---

# 11. Contribution Domain

Contribution processing is a separate subsystem.

```text
Alumnus
   │
   ▼
Contribution Submission
   │
   ├── Amount
   ├── Transaction Reference
   └── Screenshot
          │
          ▼
      Google Drive
          │
          ▼
      File ID saved
          │
          ▼
        TiDB
          │
          ▼
   Payment Verification
          │
      ┌───┴────┐
      ▼        ▼
  Verified   Rejected
```

The contribution table should contain financial metadata and a storage reference, not the actual screenshot binary. The existing database design specifies separate contribution records and controlled payment statuses. fileciteturn0file0L49-L71

---

# 12. Google Drive Storage Architecture

Google Drive is the file store for payment screenshots.

## Upload flow

For future direct website uploads:

```text
Browser
   │
   │ multipart upload
   ▼
Flask
   │
   ├── Validate file type
   ├── Validate file size
   ├── Generate safe filename
   └── Upload to private Drive folder
             │
             ▼
        Google Drive
             │
             ▼
          file_id
             │
             ▼
           TiDB
```

TiDB stores:

```text
payment_screenshot_file_id
```

rather than the screenshot itself.

## Access flow

```text
Admin Browser
     │
     ▼
Flask
     │
     ├── Verify admin authorization
     │
     ▼
Google Drive
     │
     ▼
Private screenshot
```

Screenshots must not be publicly accessible.

The database design explicitly recommends private file storage with a database reference rather than database BLOB storage. fileciteturn0file0L718-L743

---

# 13. Current Google Form Architecture

The Google Form is currently the primary collection interface.

```text
                 GOOGLE FORM
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
   Google Sheets             Google Drive
   Form responses             Screenshots
          │                       │
          └───────────┬───────────┘
                      ▼
                Import Service
                      │
              ┌───────┴────────┐
              ▼                ▼
           Validate         Normalize
              │                │
              └───────┬────────┘
                      ▼
                    TiDB
```

Because there are currently no form submissions, the initial system can use an explicit/admin-triggered import instead of real-time synchronization.

The database design intentionally treats the Google Form as an input mechanism whose columns can change independently. fileciteturn0file0L18-L18

---

# 14. Google Form Import Service

A future import service should perform:

```text
Read row
   ↓
Validate
   ↓
Normalize
   ↓
Find/create alumni
   ↓
Create meet response
   ↓
Create contribution if applicable
   ↓
Store recognition preference
   ↓
Handle volunteer information separately
```

The import should map form columns by logical field names/configuration rather than relying permanently on column positions.

The current database mapping is documented in the database design. fileciteturn0file0L545-L588

---

# 15. Volunteer Domain

Volunteers are **not alumni records**.

```text
VOLUNTEERS
     │
     ▼
ACTIVITIES
     │
     ▼
VOLUNTEER_ASSIGNMENTS
```

There is intentionally no required:

```text
alumni_id
```

on the volunteer entity.

This follows the core rule that an alumnus is not automatically a volunteer. fileciteturn0file0L24-L34

---

# 16. Volunteer Management Flow

```text
Volunteer
    │
    ▼
Organizer approves/creates volunteer
    │
    ▼
Volunteer appears in organizer dashboard
    │
    ▼
Organizer creates activity
    │
    ▼
Organizer assigns volunteer
    │
    ▼
Assignment status updated
```

Example:

```text
Activity:
Catering Coordination

Volunteers:
- Person A → Vendor coordination
- Person B → Meal count
- Person C → Dietary requirements
```

---

# 17. Activities

Activities represent organizer-side work.

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

An activity belongs to a meet.

```text
Meet
  │
  └── Activities
        │
        └── Volunteer Assignments
```

This allows one meet to have many organizer workstreams. fileciteturn0file0L423-L476

---

# 18. Future Invitation System

Invitations should be a separate subsystem.

```text
Alumni
   │
   ▼
Invitation
   │
   ├── Email
   ├── WhatsApp
   └── Future channels
```

Potential flow:

```text
Admin selects alumni
        │
        ▼
Invitation Service
        │
        ▼
Message generation
        │
        ▼
Communication provider
        │
        ▼
Invitation status
```

Possible future statuses:

```text
draft
queued
sent
delivered
opened
failed
```

The invitation record should reference both the alumnus and the meet. fileciteturn0file0L480-L509

---

# 19. Authentication and Authorization

Authentication should not be coupled directly to the alumni table.

Future structure:

```text
users
├── id
├── email
├── password_hash / external_provider_id
├── role
├── is_active
├── created_at
└── updated_at
```

Possible roles:

```text
admin
organizer
volunteer
```

The role determines access.

Example:

```text
                    USER
                     │
             ┌───────┼────────┐
             ▼       ▼        ▼
           ADMIN  ORGANIZER VOLUNTEER
             │       │        │
             ▼       ▼        ▼
          Full     Manage    Assigned
          access   operations tasks
```

Authentication remains independent of whether the person exists in `alumni`.

---

# 20. Authorization Matrix

| Capability | Public | Alumni | Volunteer | Organizer | Admin |
|---|---:|---:|---:|---:|---:|
| View public pages | ✓ | ✓ | ✓ | ✓ | ✓ |
| View public alumni information | ✓ | ✓ | ✓ | ✓ | ✓ |
| Submit meet response | ✓/future auth | ✓ | — | ✓ | ✓ |
| Submit contribution | ✓/future auth | ✓ | — | ✓ | ✓ |
| View own contribution | — | ✓ | — | ✓ | ✓ |
| View payment screenshot | — | — | — | ✓* | ✓ |
| Manage alumni | — | — | — | limited | ✓ |
| Verify contribution | — | — | — | ✓ | ✓ |
| Manage volunteers | — | — | limited | ✓ | ✓ |
| Manage activities | — | — | view/assigned | ✓ | ✓ |
| Manage invitations | — | — | — | ✓ | ✓ |
| Manage users/roles | — | — | — | — | ✓ |

`*` Only if the organizer has appropriate permission.

---

# 21. Security Architecture

## Secrets

Never hard-code:

```text
TiDB username
TiDB password
TiDB host
TiDB SSL credentials
Google API credentials
session secrets
```

Use environment variables or the hosting platform's secret management.

---

## Database Security

Use:

```text
Parameterized SQL
```

Never:

```text
"SELECT * FROM alumni WHERE email = '" + email + "'"
```

Always pass values as query parameters.

---

## Input Validation

Validate on the server even if JavaScript validates on the client.

Examples:

```text
email format
phone length
graduation year
attendee count
contribution amount
transaction reference
file type
file size
```

---

## File Upload Security

For payment screenshots:

- Allow only expected image formats.
- Enforce a maximum file size.
- Do not trust the filename.
- Generate safe internal filenames where applicable.
- Store files privately.
- Never expose raw storage paths publicly.
- Check authorization before allowing an admin to view a screenshot.

---

# 22. Configuration Architecture

Use environment variables for deployment-specific configuration.

Example categories:

```text
APPLICATION
    FLASK_ENV
    SECRET_KEY

DATABASE
    DB_HOST
    DB_PORT
    DB_NAME
    DB_USER
    DB_PASSWORD
    DB_SSL_CA

GOOGLE
    GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET
    GOOGLE_DRIVE_FOLDER_ID
    GOOGLE_SHEET_ID

EMAIL / COMMUNICATION
    future provider credentials
```

Local development and production should use different credentials.

---

# 23. Deployment Architecture

Recommended initial deployment:

```text
                 Internet
                    │
                    ▼
              HTTPS Request
                    │
                    ▼
                Render
                    │
                    ▼
              Flask Application
                 /       \
                /         \
               ▼           ▼
             TiDB      Google APIs
                       /        \
                      ▼          ▼
                 Google Sheet  Google Drive
```

Render hosts the Flask application.

TiDB is the only application database.

Google Drive handles uploaded payment screenshots.

Google Sheets/Form remains the initial external collection source.

---

# 24. Request Flow: Public Page

Example:

```text
Browser
   │
   ▼
GET /
   │
   ▼
Flask route
   │
   ▼
Jinja2 template
   │
   ▼
HTML
   │
   ▼
Browser
```

No database query should be introduced unless the page actually needs dynamic data.

---

# 25. Request Flow: Alumni Data

```text
Browser
   │
   ▼
Form submission
   │
   ▼
Flask
   │
   ▼
Validation
   │
   ▼
Alumni Service
   │
   ▼
TiDB DB layer
   │
   ▼
alumni
```

---

# 26. Request Flow: Contribution

```text
Browser
   │
   ├─────────────── amount / UTR / screenshot
   │
   ▼
Flask
   │
   ├── Validate fields
   ├── Validate screenshot
   │
   ▼
Google Drive
   │
   └── file_id
   │
   ▼
Contribution Service
   │
   ▼
TiDB
   │
   ▼
contributions
```

The payment should initially enter a non-verified state.

Only an authorized organizer/admin can change it to:

```text
verified
```

---

# 27. Request Flow: Payment Verification

```text
Admin Dashboard
      │
      ▼
Pending Contributions
      │
      ▼
Open contribution
      │
      ├── View transaction reference
      ├── View screenshot
      └── Check amount
      │
      ▼
Organizer decision
      │
      ├──────────────┐
      ▼              ▼
   Verify          Reject
      │              │
      └──────┬───────┘
             ▼
           TiDB
             │
             ▼
        Audit record
        (future)
```

Payment states are controlled by the application rather than inferred from screenshot submission. fileciteturn0file0L61-L71

---

# 28. Request Flow: Organizer Activity

```text
Organizer
   │
   ▼
Create Activity
   │
   ▼
activities
   │
   ▼
Select Volunteer
   │
   ▼
volunteer_assignments
   │
   ▼
Volunteer sees assignment
   │
   ▼
Status updates
```

---

# 29. Future Invitation Flow

```text
Organizer
    │
    ▼
Select Meet
    │
    ▼
Select Alumni
    │
    ▼
Invitation Service
    │
    ▼
Communication Provider
    │
    ▼
Email / WhatsApp / Other
    │
    ▼
Invitation status saved
```

This should be added only after the core alumni and contribution workflows are stable.

---

# 30. Project Structure

Recommended Flask structure:

```text
scss-alumni/
│
├── app.py
├── config.py
├── requirements.txt
├── .env
├── .gitignore
│
├── routes/
│   ├── public.py
│   ├── alumni.py
│   ├── contributions.py
│   ├── admin.py
│   ├── volunteers.py
│   └── invitations.py
│
├── services/
│   ├── alumni_service.py
│   ├── meet_service.py
│   ├── contribution_service.py
│   ├── volunteer_service.py
│   ├── import_service.py
│   ├── drive_service.py
│   └── invitation_service.py
│
├── db/
│   ├── connection.py
│   ├── alumni.py
│   ├── meets.py
│   ├── meet_responses.py
│   ├── contributions.py
│   ├── recognition.py
│   ├── volunteers.py
│   ├── activities.py
│   └── invitations.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── meet.html
│   ├── contribute.html
│   │
│   └── admin/
│       ├── dashboard.html
│       ├── alumni.html
│       ├── contributions.html
│       ├── volunteers.html
│       └── activities.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── images/
│
└── sql/
    ├── schema.sql
    ├── indexes.sql
    └── seed.sql
```

This is a starting structure, not a requirement to create every file immediately.

---

# 31. API / Route Philosophy

Use normal server-rendered routes for pages.

Example:

```text
GET  /
GET  /meet
GET  /contribute
GET  /alumni
GET  /admin
```

Use POST routes for state-changing operations:

```text
POST /contribute
POST /admin/contributions/<id>/verify
POST /admin/contributions/<id>/reject
POST /admin/volunteers
POST /admin/activities
```

Use JSON endpoints only where asynchronous UI behavior provides a clear benefit.

Do not turn the application into a REST API unnecessarily during the MVP.

---

# 32. Database Transaction Boundaries

Transactions are especially important for contribution operations.

Example:

```text
BEGIN
    update contribution
    update verification metadata
    insert audit record
COMMIT
```

If any step fails:

```text
ROLLBACK
```

The application should never leave a contribution half-updated.

---

# 33. Public vs Private Data Boundary

The backend should have separate query paths for public and private information.

Bad pattern:

```text
SELECT *
FROM alumni
```

followed by filtering fields in the template.

Better:

```text
Public query
    ↓
Only fields explicitly approved for public display
```

For example:

```text
full_name
graduation_year
course
organization
designation
```

Private information should never be sent to the browser unless the authenticated user is authorized to see it.

The database design explicitly classifies email, phone, payment references, screenshots, and internal notes as private. fileciteturn0file0L592-L632

---

# 34. MVP Boundary

The first version should implement only what is necessary.

## Phase 1

```text
✓ Flask application
✓ Public website
✓ TiDB connection
✓ Alumni table
✓ Meets table
✓ Meet responses
✓ Contributions
✓ Recognition preferences
✓ Basic admin dashboard
✓ Contribution verification
✓ Google Drive screenshot references
```

## Phase 2

```text
✓ Volunteer management
✓ Activities
✓ Volunteer assignments
✓ Better dashboard/analytics
```

## Phase 3

```text
✓ Authentication improvements
✓ Google Form/Sheet import
✓ Invitations
✓ Email communication
✓ WhatsApp integration if required
```

## Phase 4

```text
✓ Alumni directory
✓ Gallery
✓ Multiple meets
✓ Advanced analytics
✓ Audit logs
```

The database design similarly recommends keeping the initial database small and adding activities, assignments, invitations, users, audit logs, and payment settings as the corresponding features become necessary. fileciteturn0file0L884-L919

---

# 35. What Should NOT Be Added Initially

Avoid premature complexity such as:

```text
React
Vue
Angular
ORM
Microservices
Redis
Celery
Kubernetes
Separate API server
Separate frontend server
S3
Complex event bus
```

None of these are necessary for the first version.

The system should remain:

```text
One Flask application
        +
One TiDB database
        +
Google Drive
        +
Google Form/Sheet
```

This is enough to build the initial platform cleanly.

---

# 36. Architecture Decision Summary

| Component | Decision |
|---|---|
| Frontend | HTML + CSS + Vanilla JS |
| Templates | Jinja2 |
| Backend | Flask |
| Database | TiDB |
| Database access | Raw SQL |
| ORM | None |
| MySQL server | None |
| Local DB fallback | None |
| Payment screenshot storage | Google Drive |
| Form collection | Google Form |
| Form response storage | Google Sheet initially |
| Hosting | Render |
| Authentication | Separate user/auth layer |
| Alumni ↔ Volunteer relationship | None required |
| Multiple meets | Supported |
| Invitations | Future module |
| Audit logs | Future module |

---

# 37. Final System Map

```text
                                ┌──────────────────────┐
                                │       INTERNET       │
                                └──────────┬───────────┘
                                           │
                                           ▼
                                ┌──────────────────────┐
                                │     WEB BROWSER      │
                                │                      │
                                │ HTML / CSS / JS      │
                                └──────────┬───────────┘
                                           │
                                           │ HTTPS
                                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FLASK APPLICATION                               │
│                                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │
│  │   Public    │ │    Admin    │ │  Organizer  │ │ Future APIs /  │  │
│  │   Routes    │ │   Routes    │ │   Routes    │ │ Integrations   │  │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └────────┬────────┘  │
│         └────────────────┼──────────────┼──────────────────┘           │
│                          ▼              ▼                              │
│                 ┌──────────────────────────────┐                       │
│                 │       SERVICE LAYER          │                       │
│                 │                              │                       │
│                 │ Alumni                       │                       │
│                 │ Meet                         │                       │
│                 │ Contributions                │                       │
│                 │ Volunteers                   │                       │
│                 │ Activities                   │                       │
│                 │ Import                       │                       │
│                 │ Invitations                  │                       │
│                 └──────────────┬───────────────┘                       │
│                                │                                       │
│                 ┌──────────────┼──────────────┐                        │
│                 ▼              ▼              ▼                        │
│          ┌────────────┐ ┌──────────────┐ ┌──────────────┐              │
│          │ TiDB DB    │ │ Google Drive │ │ Google Sheet │              │
│          │ Layer      │ │ Service      │ │ Import       │              │
│          └─────┬──────┘ └──────┬───────┘ └──────┬───────┘              │
└────────────────┼───────────────┼────────────────┼──────────────────────┘
                 │               │                │
                 ▼               ▼                ▼
          ┌────────────┐  ┌──────────────┐  ┌──────────────┐
          │    TiDB    │  │ Google Drive │  │ Google Form  │
          │            │  │              │  │      ↓       │
          │ Alumni     │  │ Screenshots  │  │ Google Sheet │
          │ Meets      │  │              │  │              │
          │ Responses  │  └──────────────┘  └──────────────┘
          │ Contrib.   │
          │ Volunteers │
          │ Activities │
          │ Invitations│
          └────────────┘
```

## Architectural Rule

The platform should remain a **single Flask application with clear internal boundaries**, not a collection of separate services.

The key separation is:

```text
ALUMNI
  ≠
VOLUNTEERS

ALUMNI PROFILE
  ≠
MEET RESPONSE

CONTRIBUTION DATA
  ≠
PAYMENT SCREENSHOT

DATABASE
  ≠
FILE STORAGE

GOOGLE FORM
  ≠
APPLICATION DATABASE
```

These boundaries keep the initial system simple while allowing it to grow into a broader SC&SS JNU alumni platform.

---

# 38. Documentation Maintenance

`PROJECT_INSTRUCTIONS.md` is the first-read project instruction file.

Whenever the architecture changes, this document must be updated.

Examples of changes requiring an update:

- New application component
- New external integration
- New storage provider
- New service/module
- New deployment dependency
- New authentication/authorization mechanism
- New request/data flow
- Removal or replacement of an existing component

After an architectural change, check `PROJECT_INSTRUCTIONS.md`, `database_design.md`, and `design.md` for consistency.

Do not leave important architectural decisions only in chat history.
