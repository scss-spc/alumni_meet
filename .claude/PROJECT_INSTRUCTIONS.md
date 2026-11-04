**# SC&SS JNU Alumni Meet — Project Instructions & Source of Truth**

**## Purpose**

This file is the persistent project-level instruction document for the SC&SS JNU Alumni Meet website.

It must be treated as the **\*\*first-read project context\*\*** whenever making changes to the architecture, database, UI/UX, features, workflows, or implementation decisions.

The project has three primary planning documents:

\`\`\`text

PROJECT_INSTRUCTIONS.md   ← read first

        │

        ├── architecture.md

        └── database_design.md

        └── design.md

\`\`\`

\`PROJECT_INSTRUCTIONS.md\` contains project-wide rules and decisions.

The other documents contain the detailed architecture, database model, and visual design.

**---**

**# 1. Project Identity**

Project:

**\*\*SC&SS JNU Alumni Meet Platform\*\***

Institution:

**\*\*School of Computer and Systems Sciences (SC&SS), Jawaharlal Nehru University (JNU)\*\***

The platform starts as an Alumni Meet management and contribution-tracking system and is intended to evolve into a broader alumni platform.

**---**

**# 2. Current Product Scope**

The current system is primarily concerned with:

\- Alumni information

\- Alumni Meet participation

\- Contribution tracking

\- Payment verification

\- Dietary requirements

\- Suggestions

\- Public recognition preferences

\- Organizer/volunteer management

\- A foundation for future invitations and communication

The system must remain small and understandable in the initial implementation.

**---**

**# 3. Critical Current Decisions**

These are project decisions and must not be silently changed.

**## 3.1 Technology**

\`\`\`text

Backend: Flask / Python

Frontend:

HTML

CSS

Vanilla JavaScript

Jinja2

Database:

TiDB

Database access:

Raw SQL

ORM:

None

MySQL server:

None

SQLite fallback:

None

\`\`\`

TiDB's MySQL-compatible protocol does **\*\*not\*\*** mean that the project should introduce a MySQL server.

**---**

**## 3.2 Storage**

Payment screenshots are stored in:

\`\`\`text

Google Drive

\`\`\`

TiDB stores a reference such as:

\`\`\`text

payment_screenshot_file_id

\`\`\`

The screenshot itself must not be stored as a database BLOB.

**---**

**## 3.3 Google Form is the current collection interface**

The current Google Form is the input mechanism for alumni/meet/contribution information.

Current flow:

\`\`\`text

Google Form

      ↓

Google Sheet

      ↓

Import / processing

      ↓

TiDB

\`\`\`

Payment screenshots are associated with Google Drive.

The website does **\*\*not\*\*** currently provide a custom contribution/payment form.

The website's contribution CTA should direct users to the configured Google Form.

Do not introduce a custom payment form unless the project requirements explicitly change.

**---**

**## 3.4 Current form has no entries**

At the time this instruction file was created, the Google Form has no submissions.

Therefore:

\- Do not design around existing data that does not exist.

\- Do not invent alumni records.

\- Do not invent contribution statistics.

\- Do not invent payment history.

\- Do not invent attendance numbers.

Placeholder/demo data may be used only when clearly marked as sample data during development.

**---**

**# 4. Alumni and Volunteer Rule**

This is a critical domain rule.

**\*\*Alumni and volunteers are separate concepts.\*\***

An alumnus is not automatically a volunteer.

A volunteer is not assumed to be an alumnus.

There must not be a required alumni-to-volunteer relationship merely because someone helps organize the meet.

Conceptually:

\`\`\`text

ALUMNI

        separate from

VOLUNTEERS

\`\`\`

Volunteer activities are organizer-side functionality.

Alumni should not see volunteer management as part of their normal experience.

**---**

**# 5. Alumni Experience**

Alumni are primarily users/participants of the Alumni Meet.

Their experience concerns:

\`\`\`text

Meet information

Registration / participation

Guest information

Dietary information

Suggestions

Contribution

Public recognition preference

Future alumni features

\`\`\`

They are not expected to manage organizer activities.

**---**

**# 6. Volunteer Experience**

Volunteers exist to help organize the event.

Their domain is:

\`\`\`text

Volunteers

    ↓

Activities

    ↓

Assignments

    ↓

Task/status management

\`\`\`

This should remain separate from the alumni-facing experience.

**---**

**# 7. Contribution Workflow**

Current contribution workflow:

\`\`\`text

Alumnus

   ↓

Google Form

   ↓

Payment

   ↓

UTR / transaction reference

   ↓

Payment screenshot upload

   ↓

Google Drive

   ↓

Google Sheet / Form response

   ↓

Import / processing

   ↓

TiDB

   ↓

Organizer verification

\`\`\`

The website does not currently collect:

\- UTR

\- Payment screenshot

\- Payment amount through a custom form

Those are collected through Google Forms.

The website may display:

\`\`\`text

Support the Meet

[ Contribute via Google Form ]

\`\`\`

**---**

**# 8. Database Rules**

The database should preserve these boundaries:

\`\`\`text

Alumni profile

    ≠

Meet-specific response

Alumni

    ≠

Volunteer

Contribution

    ≠

Payment screenshot

Database

    ≠

File storage

Google Form

    ≠

Application database

\`\`\`

Contributions are independent records because one alumnus may potentially make multiple contributions.

Meet-specific information belongs to the meet response.

Private information must not become public merely because an alumnus opts for public recognition.

**---**

**# 9. Public Privacy Rule**

The following are private by default:

\`\`\`text

Email

Phone

Payment details

UTR / transaction references

Payment screenshots

Internal organizer information

\`\`\`

Public recognition must be explicit.

The public website must only expose information that is intentionally approved for public display.

Never use:

\`\`\`text

SELECT \*

\`\`\`

and expose the entire alumni record to a public page.

**---**

**# 10. Design Direction**

The selected visual direction is:

**\*\*JNU × Modern Tech, grounded in the SC&SS placement-brochure identity\*\***

The primary visual reference is the **\*\*SC&SS JNU Placement Brochure 2026–27\*\***.

The previous maroon/red direction is discarded. The website uses the brochure's navy, gold, cream, serif/sans typography, editorial grids, section ribbons, gold rules, real campus photography, and restrained concentric-circle motif.

The website should feel:

\`\`\`text

Academic

Institutional

Editorial

Human

Modern

Timeless

\`\`\`

It should not feel like:

\`\`\`text

AI-generated

Generic startup

SaaS landing page

Corporate consulting site

Generic conference template

\`\`\`

Avoid:

\- Neon gradients

\- Excessive glassmorphism

\- Generic AI imagery

\- AI-generated people

\- Generic tech stock imagery

\- Decorative 3D objects

\- Excessive rounded cards

\- Giant marketing slogans

\- Excessive animation

Prefer real SC&SS/JNU photography and authentic institutional material.

**---**

**# 11. Design System Direction

The current and authoritative visual direction is the **SC&SS Editorial Heritage** theme defined in `design.md`.

Use the SC&SS/JNU placement-brochure-inspired palette:

```text
Navy
#102653

Deep Navy
#0B1B3A

Warm Ivory
#F6F1E7

Paper
#FBF9F4

Muted Gold
#C7A84B

Dark Ink
#182033

Muted Ink
#5E6270

White
#FFFFFF
```

The previously rejected maroon/red visual direction must not be reintroduced.

Typography direction:

```text
Display:
Playfair Display

Body/UI:
Inter
```

Detailed visual rules, component styling, responsive behaviour, and accessibility requirements are defined in `design.md`.

`design.md` is the authoritative source for detailed visual implementation decisions.

**---**

# 12. Public Website Philosophy**

The public website should tell a story rather than look like a feature catalogue.

The homepage should generally follow:

\`\`\`text

Navigation

    ↓

Hero

    ↓

Meet introduction

    ↓

SC&SS / JNU story

    ↓

Alumni / generations

    ↓

Meet information

    ↓

Contribution CTA

    ↓

Contact / closing statement

    ↓

Footer

\`\`\`

The design should use real content and real institutional material whenever available.

Do not invent institutional history, statistics, rankings, alumni counts, faculty counts, or other factual claims for visual purposes.

**---**

**# 13. Admin / Organizer Philosophy**

The public website and organizer dashboard serve different purposes.

Public:

\`\`\`text

Human

Editorial

Spacious

Story-driven

\`\`\`

Admin:

\`\`\`text

Functional

Information-dense

Searchable

Filterable

Operational

\`\`\`

The admin dashboard should prioritize:

\- Alumni records

\- Attendance

\- Contributions

\- Payment verification

\- Volunteers

\- Activities

\- Future invitations

**---**

**# 14. Future Features**

The architecture should allow:

\`\`\`text

Multiple Alumni Meets

Alumni directory

Volunteer management

Organizer activities

Invitation system

Email communication

WhatsApp communication

Gallery

Audit logs

Advanced analytics

\`\`\`

Future features should not be added to the MVP merely because the architecture supports them.

Add functionality when there is an actual requirement.

**---**

**# 15. Implementation Principles**

**## Keep the application simple**

Preferred:

\`\`\`text

One Flask application

\+

One TiDB database

\+

Google Drive

\+

Google Form / Sheet

\`\`\`

Do not introduce unnecessary infrastructure.

Avoid prematurely adding:

\`\`\`text

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

Event buses

\`\`\`

unless a concrete requirement justifies them.

**---**

**## Database access**

Use:

\`\`\`text

Route

  ↓

Service

  ↓

DB function / repository

  ↓

Parameterized SQL

  ↓

TiDB

\`\`\`

Do not put large SQL/business-logic blocks directly into routes.

Never concatenate user input into SQL.

**---**

**# 16. Configuration and Secrets**

Never commit secrets to source control.

Examples:

\`\`\`text

TiDB credentials

TiDB SSL credentials

Google credentials

Google Drive identifiers

Google Sheet identifiers

Flask SECRET_KEY

Future email/WhatsApp credentials

\`\`\`

Use environment variables or deployment-platform secret management.

**---**

**# 17. Change Management Rule**

This section is mandatory.

Whenever a new decision, requirement, constraint, workflow, architecture component, database entity, UI rule, or integration is introduced, determine whether it changes any existing project documentation.

If it does, update the relevant document(s).

At minimum, check:

\`\`\`text

PROJECT_INSTRUCTIONS.md

architecture.md

database_design.md

design.md

\`\`\`

Do not allow implementation decisions to exist only in chat.

**---**

**# 18. What Belongs in Each Document**

**## PROJECT_INSTRUCTIONS.md**

Contains:

\- Project-wide rules

\- Non-negotiable decisions

\- Current scope

\- Important constraints

\- Cross-document consistency rules

\- Current product assumptions

This is the first-read document.

**---**

**## architecture.md**

Contains:

\- System architecture

\- Application components

\- Data flows

\- Service boundaries

\- External integrations

\- Deployment architecture

\- Security architecture

\- Request flows

\- Future system components

If a new component or integration is introduced, update this file.

**---**

**## database_design.md**

Contains:

\- Entities

\- Tables

\- Columns

\- Relationships

\- Constraints

\- Indexes

\- Data lifecycle

\- Privacy classification

\- Google Form mapping

\- Database-related future extensions

If a feature changes the data model, update this file.

**---**

**## design.md**

Contains:

\- Visual identity

\- Color system

\- Typography

\- Layout

\- Components

\- Navigation

\- Page structure

\- Responsive behavior

\- Accessibility

\- Public/admin UX direction

If a new UI pattern or design decision is introduced, update this file.

**---**

**# 19. Cross-Document Consistency**

The three detailed documents must not contradict one another.

Before making a change, check whether it affects:

\`\`\`text

Architecture

Database

Design

\`\`\`

Examples:

**### Example 1**

A new invitation provider is introduced.

Update:

\`\`\`text

PROJECT_INSTRUCTIONS.md

architecture.md

database_design.md   ← if data/schema changes

design.md            ← if UI changes

\`\`\`

**### Example 2**

A new database entity is introduced.

Update:

\`\`\`text

PROJECT_INSTRUCTIONS.md

database_design.md

architecture.md      ← if architecture/data flow changes

design.md            ← if a UI is introduced

\`\`\`

**### Example 3**

A new public page is introduced.

Update:

\`\`\`text

PROJECT_INSTRUCTIONS.md

design.md

architecture.md      ← if routing/application architecture changes

database_design.md   ← only if new data is required

\`\`\`

**---**

**# 20. Documentation Update Protocol**

After completing a meaningful change:

1\. Identify what changed.

2\. Identify which document(s) are affected.

3\. Update the affected document(s).

4\. Add the decision to this instruction file if it is project-wide or non-obvious.

5\. Check for contradictions with the other documents.

6\. Keep the documents describing the current state, not obsolete plans.

Do not blindly append duplicate information.

Prefer modifying the existing section when the decision changes an earlier decision.

**---**

**# 21. Conflict Resolution**

If two project documents conflict:

1\. Prefer the most recent explicit project decision.

2\. Check the current implementation/requirements.

3\. Update the affected documents so they agree.

4\. Do not silently choose one interpretation and leave the contradiction in place.

When a decision is genuinely unresolved, mark it explicitly as:

\`\`\`text

DECISION PENDING

\`\`\`

Do not invent a decision.

**---**

**# 22. Status Labels**

When useful, decisions may be classified as:

\`\`\`text

DECIDED

CURRENT

FUTURE

DEFERRED

PENDING

\`\`\`

Do not treat future/deferred features as current requirements.

**---**

**# 23. Current State Snapshot**

At the time of this document:

\`\`\`text

Project:

SC&SS JNU Alumni Meet Platform

Frontend:

HTML + CSS + Vanilla JS + Jinja2

Backend:

Flask / Python

Database:

TiDB

ORM:

None

MySQL:

Not used

SQLite fallback:

Not used

Payment screenshot storage:

Google Drive

Current collection mechanism:

Google Form

Form response storage:

Google Sheet

Current form submissions:

None

Alumni:

Separate entity

Volunteers:

Separate entity

Alumni automatically volunteers:

No

Website contribution form:

Not currently implemented

Website contribution CTA:

Links to Google Form

Invitation system:

Future

Public alumni directory:

Future

Organizer activity management:

Future/current architecture support, introduced when needed

\`\`\`

**---**

**## 23.1 Design Revision**

The initial design proposal used a maroon/red palette. That decision was rejected.

The current design is based on the **\*\*SC&SS JNU Placement Brochure 2026–27\*\***, whose visual language uses navy \`#0B1F4D\`, gold \`#D4A745\`, warm cream \`#F7F3EA\`, Playfair Display, Inter, editorial layouts, section ribbons, gold rules, and real JNU/SC&SS photography.

This is the current design baseline.

**---**

**# 24. Responsive Implementation Rule

Responsive behaviour is a mandatory project requirement.

The authoritative responsive specification is the **Responsive Design Contract** in `design.md`.

The rules in `design.md` are not optional design suggestions. They define the expected frontend behaviour across mobile, tablet, and desktop.

## 24.1 Required Responsive States

```text
MOBILE
< 768px

TABLET
768px–1023px

DESKTOP
>= 1024px
```

Also check narrow-phone widths:

```text
320px
360px
375px
390px
430px
```

## 24.2 Mandatory Rules

Frontend implementations must:

- prevent unintended horizontal page overflow
- keep primary content inside the viewport
- allow text to wrap naturally
- allow grids and flex layouts to reflow
- keep images within their containers
- preserve important content on mobile
- maintain readable typography
- maintain usable touch targets
- preserve the SC&SS Editorial Heritage visual system
- use fluid/responsive layout techniques for primary page structure
- adapt navigation, hero, grids, cards, forms, images, and typography to the viewport

Frontend implementations must not:

- rely on fixed desktop widths for primary content
- use fixed positioning as the primary page-layout mechanism
- allow images or components to widen the page beyond the viewport
- create a separate mobile visual identity
- simply shrink the desktop layout without changing its composition where necessary
- hide important content solely to make mobile shorter
- introduce horizontal page scrolling for normal website use
- introduce a different mobile colour or typography system

## 24.3 Responsive Definition of Done

A responsive frontend change is **not complete** merely because media queries or responsive CSS have been added.

It is complete only when the implementation has been verified against the responsive acceptance criteria defined in `design.md`.

At minimum, verify:

```text
[ ] 320px
[ ] 360px
[ ] 390px
[ ] 430px
[ ] 768px
[ ] 1024px
[ ] 1280px

[ ] No horizontal page overflow
[ ] No clipped primary content
[ ] No overflowing images
[ ] No overflowing buttons
[ ] No broken navigation
[ ] No broken grids
[ ] No broken forms
[ ] Typography remains readable
[ ] Important content remains present
[ ] Visual identity remains consistent
```

A page that works on desktop but fails the required mobile checks is **not complete**.

## 24.4 Change Requirement

Any frontend change affecting:

```text
layout
width
height
grid
flexbox
positioning
typography
navigation
images
cards
forms
buttons
spacing
```

must be checked at both mobile and desktop widths.

If a shared component is changed, verify the pages that use that component where practical.

## 24.5 No Silent Exceptions

If a component cannot follow the normal responsive rules, document the exception explicitly:

```text
RESPONSIVE EXCEPTION

Component:
Reason:
Affected viewport:
Why the normal rule cannot be used:
Approved alternative:
```

Do not silently ignore a responsive requirement.

## 24.6 Automated Tests

Automated responsive tests should be maintained separately from `design.md`.

`design.md` defines **what correct responsive behaviour means**.

The test suite defines **whether the implementation currently satisfies those requirements**.

When responsive test infrastructure is introduced, it should verify the acceptance criteria from `design.md` at the required viewport widths.

Do not weaken or remove a responsive test merely because the current implementation fails it. Fix the implementation or explicitly update the documented requirement.

## 24.7 Documentation Boundary

Keep responsibilities separate:

```text
PROJECT_INSTRUCTIONS.md
    ↓
Project-level responsive requirement

design.md
    ↓
Detailed responsive design contract

Frontend HTML/CSS/JS
    ↓
Actual implementation

Responsive test suite
    ↓
Automated verification
```

Do not duplicate the complete responsive specification across all documents.

`PROJECT_INSTRUCTIONS.md` establishes the requirement and enforcement process; `design.md` contains the detailed visual and responsive contract.

**---**

# 25. Golden Rule**

When building or changing this project:

*>* **\*\*Do not rely on chat history as the only place where an important project decision exists.\*\***

Important decisions belong in the project documentation.

The documentation should remain a living representation of the actual system.

Before substantial implementation work:

\`\`\`text

Read PROJECT_INSTRUCTIONS.md

        ↓

Read relevant detailed document(s)

        ↓

Make the change

        ↓

Update affected documentation

        ↓

Continue implementation

\`\`\`