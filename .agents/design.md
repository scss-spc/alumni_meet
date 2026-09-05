# SC&SS JNU Alumni Meet Platform — Design System

## 1. Design Intent

The SC&SS JNU Alumni Meet website should feel like a digital extension of the School's existing visual identity, not a generic alumni-event template.

The primary visual reference is the **SC&SS JNU Placement Brochure 2026–27**.

The brochure establishes a much stronger direction than the previous website concept:

- Deep JNU/SC&SS navy as the anchor color
- Warm cream/off-white page backgrounds
- Restrained gold accents
- Serif display typography paired with a clean sans-serif
- Strong horizontal section ribbons
- Editorial grids
- Real campus photography
- Thin gold rules
- Small uppercase labels with generous tracking
- White content cards sitting on cream
- Concentric-circle / geometric motifs used sparingly
- Strong visual hierarchy without decorative clutter

The alumni website should **translate this language to the web**, not copy the brochure page-for-page.

---

# 2. Primary Reference

Reference:

**SC&SS · JNU · Placement Brochure 2026–27**

The cover uses a dark navy field, the JNU seal, cream/white typography, gold accents, and a large photograph of the SC&SS building.

The interior pages consistently use a cream background, navy section ribbons, gold rules/details, serif headings, and structured content blocks.

The campus page demonstrates the intended photography treatment: multiple real JNU photographs arranged in a clean editorial grid.

These characteristics should form the basis of the Alumni Meet website.

---

# 3. Visual Personality

The website should communicate:

```text
JNU
Institution
History
Academic credibility
        +
SC&SS
Computer science
Systems
Technology
Precision
        +
Alumni
People
Memory
Community
Continuity
```

The resulting personality should be:

```text
Editorial
Academic
Warm
Institutional
Confident
Modern
Human
```

It should NOT feel:

```text
AI-generated
Startup-like
SaaS-like
Corporate
Overly futuristic
Generic event-template
```

---

# 4. Color System

The previous maroon/red direction is **discarded**.

The website should use the navy/gold/cream visual language established by the SC&SS placement brochure.

## 4.1 Primary Navy

```text
#0B1F4D
```

Use for:

- Header
- Section ribbons
- Major headings where appropriate
- Primary navigation states
- Dark feature sections
- Important UI elements
- Footer
- Large statistic bands

This is the principal identity color.

---

## 4.2 Gold Accent

```text
#D4A745
```

Use sparingly for:

- Small rules
- Section accents
- Numbers
- Dates
- Active indicators
- Important metadata
- Decorative lines
- Selected UI states

Gold is an accent, not a body-text color.

Never use gold for long paragraphs.

---

## 4.3 Warm Cream

```text
#F7F3EA
```

Primary page background.

This should replace a generic pure-white website background wherever possible.

It gives the interface the same warm editorial quality seen in the brochure.

---

## 4.4 White

```text
#FFFFFF
```

Use for:

- Content cards
- Form surfaces
- Photo frames
- Navigation surfaces where appropriate
- Contrast sections

White should generally sit against cream rather than dominate the entire page.

---

## 4.5 Body Text

```text
#1A1A1A
```

Use for running text.

---

## 4.6 Muted Text

```text
#5A6478
```

Use for:

- Metadata
- Captions
- Secondary information
- Supporting UI text

---

## 4.7 Supporting Blues

Where additional visual differentiation is required:

```text
#2E4D8B
#5B7BB8
#8FA8D4
```

These should be used only where necessary, particularly for data visualization or subtle interface states.

Do not turn the site into a blue gradient.

---

# 5. Color Rules

### Always

```text
Navy + Cream + White + Gold
```

### Sometimes

```text
Supporting blues
```

### Never as the main identity

```text
Red
Maroon
Teal
Cyan
Neon purple
Neon blue
Black + yellow
```

Do not introduce a new dominant color without updating this design document.

---

# 6. Typography

The placement brochure's typography is a strong reference and should be carried into the website.

Use two families.

## 6.1 Display / Editorial Font

Preferred:

```text
Playfair Display
```

Fallback:

```text
'Playfair Display', 'Source Serif Pro', Georgia, serif
```

Use for:

- Hero titles
- Major page headings
- Editorial statements
- Important numbers
- Historical moments
- Section introductions

The serif is important because it gives the site a more institutional and editorial character.

---

## 6.2 UI / Body Font

Preferred:

```text
Inter
```

Fallback:

```text
Inter, system-ui, sans-serif
```

Use for:

- Navigation
- Labels
- Buttons
- Forms
- Body text
- Tables
- Metadata
- Admin interface

---

# 7. Typography Style

The brochure uses small uppercase labels with generous tracking.

Carry that pattern into the website.

Example:

```text
SCHOOL OF COMPUTER & SYSTEMS SCIENCES
```

Then:

```text
Alumni Meet 2026
```

Then supporting text.

The hierarchy should generally be:

```text
EYEBROW
small / uppercase / tracked

H1
large serif

BODY
clean sans-serif

METADATA
small / muted / tracked
```

Avoid making every heading uppercase.

---

# 8. Signature Visual Elements

The website should use several recognizable elements from the brochure.

## 8.1 Navy Section Ribbon

A navy horizontal bar can introduce major sections.

Example:

```text
┌─────────────────────────────────────────────┐
│  02   THE ALUMNI MEET                       │
└─────────────────────────────────────────────┘
```

The ribbon can have the brochure-inspired angled/diagonal end treatment.

This should be used for major sections, not every small subsection.

---

## 8.2 Gold Rule

A short gold line should sit near major headings.

Example:

```text
ABOUT THE MEET

Alumni Meet 2026
────────
```

The rule should be short and intentional.

---

## 8.3 Concentric Circle Motif

The brochure uses concentric arcs/circles as a subtle signature.

For the website:

- Use as a background watermark
- Use in the hero
- Use on major section transitions
- Use in empty visual space

Opacity should remain low.

The motif must never compete with the content.

---

## 8.4 Vertical Gold Rule

A thin gold vertical rule can be used selectively in editorial sections.

Example:

```text
│
│  About the School
│
│  Content...
```

This is particularly useful for:

- History
- Timeline
- Alumni stories
- Quotes

Do not use it everywhere.

---

# 9. Photography

Photography should be one of the major visual elements of the site.

The brochure demonstrates that SC&SS/JNU's own campus imagery works very well.

Prefer:

1. SC&SS building
2. JNU campus
3. Alumni photographs
4. Historical SC&SS photographs
5. Alumni Meet photographs
6. Faculty photographs where relevant

Avoid:

- Stock photos
- Generic laptop photos
- Generic office photos
- AI-generated people
- Generic technology imagery

If there is no suitable photograph, use typography, whitespace, rules, or the concentric motif instead of filling the space with generic imagery.

---

# 10. Image Treatment

Images should generally be:

- Rectangular
- Editorially cropped
- High quality
- Naturally colored
- Free of heavy filters

Avoid:

```text
Huge shadow
Heavy gradient overlay
Excessive rounded corners
Artificial glow
```

Photo grids can use small or no gaps depending on the composition.

---

# 11. Homepage

The homepage should feel closer to a **digital editorial publication** than a startup landing page.

Recommended structure:

```text
01  Header
02  Hero
03  About the Alumni Meet
04  SC&SS / JNU story
05  Alumni generations
06  Meet information
07  Contribution
08  Closing / contact
09  Footer
```

---

# 12. Header

The header should be visually connected to the brochure.

Suggested structure:

```text
┌─────────────────────────────────────────────────────┐
│ SC&SS                         ALUMNI MEET   ABOUT   │
│ School of Computer & Systems Sciences       ...    │
└─────────────────────────────────────────────────────┘
```

Use:

- Navy text
- Cream background
- Thin gold detail
- Official logo/seal when the correct asset is available

The header should become slightly more compact when scrolling.

Do not use a giant sticky navbar.

---

# 13. Hero

The hero should be the strongest visual section.

Use a real SC&SS/JNU photograph.

Preferred direction:

```text
┌─────────────────────────────────────────────────────┐
│                                                     │
│ SCHOOL OF COMPUTER & SYSTEMS SCIENCES                │
│                                                     │
│ Alumni Meet 2026                    ┌────────────┐  │
│                                     │            │  │
│ Returning to the place where        │ SC&SS /    │  │
│ many of our journeys began.         │ JNU PHOTO  │  │
│                                     │            │  │
│ 29 AUGUST 2026                      └────────────┘  │
│                                                     │
│ [ REGISTER ]                                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

The exact copy remains content-dependent.

The hero should not use generic slogans such as:

```text
RECONNECT.
REIMAGINE.
REDEFINE.
```

The language should sound like a university alumni invitation.

---

# 14. Hero Visual Treatment

The brochure cover provides the strongest reference.

Possible treatment:

```text
Navy field
      +
Large campus photograph
      +
Cream/white typography
      +
Gold date/accent
      +
Subtle concentric motif
```

A full-bleed photograph is acceptable.

However, the website should not simply recreate the PDF cover.

The web hero can use a more responsive composition.

---

# 15. About the Meet

This section should have strong editorial typography.

Example:

```text
01  ABOUT THE MEET

A return to SC&SS.

Years after leaving the School,
the connection continues.

[short paragraph]
```

Use a two-column layout where useful.

Do not put this content inside a generic card.

---

# 16. SC&SS / JNU Story

Use a layout inspired by the brochure's institution page.

Recommended:

```text
┌──────────────────────┬────────────────────────────┐
│                      │ INSTITUTION                │
│ SC&SS/JNU photograph │                            │
│                      │ A short verified history   │
│                      │ of JNU and SC&SS.          │
│                      │                            │
└──────────────────────┴────────────────────────────┘
```

Follow with a navy statistic band only when actual verified statistics exist.

Do not invent statistics.

---

# 17. Alumni Generations

The alumni meet is fundamentally about continuity.

Use graduation years as a visual device.

Example:

```text
1980       1990       2000       2010       2020       2026
  │          │          │          │          │          │
──●──────────●──────────●──────────●──────────●──────────●
```

The timeline should be understated.

It should feel like an institutional archive rather than a software timeline component.

---

# 18. Alumni Profiles

If public alumni recognition is enabled, use restrained editorial cards.

Example:

```text
┌────────────────────────────┐
│                            │
│       PHOTO                │
│                            │
│  FULL NAME                 │
│  MCA · 2012                │
│  Current Organization      │
│  Current Position          │
│                            │
└────────────────────────────┘
```

Only information explicitly approved for public recognition may appear.

Private email, phone, payment, and other internal fields must never appear.

---

# 19. Meet Information

Use a structured editorial block rather than four large marketing cards.

Example:

```text
MEET DETAILS

29 AUGUST 2026
────────────────────

VENUE
[Confirmed venue]

TIME
[Confirmed time]

REGISTRATION
[Registration information]
```

Use navy headings and gold rules.

---

# 20. Contribution

Contribution currently happens through Google Forms.

Therefore the website does not contain a payment form in the MVP.

Use a strong but simple CTA:

```text
SUPPORT THE MEET

Help us bring the SC&SS community together.

Your contribution supports the Alumni Meet
and its arrangements.

[ CONTRIBUTE VIA GOOGLE FORM ]
```

The CTA should open the configured Google Form.

Do not place these fields on the website:

```text
UTR
Payment screenshot
UPI transaction form
Payment verification form
```

Those remain in Google Forms / Google Drive.

---

# 21. Contribution CTA Design

This can be a navy section with cream text and gold accents.

Example:

```text
┌─────────────────────────────────────────────────────┐
│                                                     │
│ SUPPORT THE MEET                                    │
│                                                     │
│ Help us bring the SC&SS community together.         │
│                                                     │
│                         [ CONTRIBUTE VIA FORM ]     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

This provides a strong visual break without introducing another color.

---

# 22. Footer

The footer should resemble an institutional closing page.

Use navy background.

Example:

```text
SC&SS
School of Computer & Systems Sciences
Jawaharlal Nehru University, New Delhi

Alumni Meet 2026

About     Alumni     Meet     Contact

──────────────────────────────────────

School of Computer & Systems Sciences
Jawaharlal Nehru University
```

Gold can be used for small rules and accents.

---

# 23. Cards

Cards should be used more deliberately than in the previous design.

The brochure uses white cards against cream.

Carry that pattern into the web interface.

Card:

```text
background: white
border: subtle navy
radius: modest
padding: generous
shadow: none or extremely subtle
```

Do not turn every section into cards.

---

# 24. Border Radius

Use restrained corner radii.

Recommended direction:

```text
Small radius
```

Avoid:

```text
Large pill shapes
Fully rounded cards
Bubble UI
```

The brochure is structured and editorial, not playful.

---

# 25. Buttons

Primary button:

```text
[ REGISTER FOR THE MEET ]
```

Style:

- Navy fill
- Cream/white text
- Small/modest radius
- Clear typography
- Gold hover/detail where appropriate

Secondary button:

```text
[ LEARN MORE ]
```

Can use a navy border and transparent/cream background.

Avoid excessive pill buttons.

---

# 26. Data and Statistics

When actual alumni data becomes available, statistics can be presented visually.

Examples:

```text
2012
MCA

47
Alumni attending

₹X
Verified contributions
```

Numbers can use the serif display font.

Gold should be used for emphasis.

Do not show statistics until there is real data.

---

# 27. Admin Dashboard

The admin dashboard should use the same palette but be more functional.

Suggested:

```text
Navy sidebar
Cream workspace
White content surfaces
Gold status accents
```

Example:

```text
┌──────────────┬──────────────────────────────────────┐
│ SC&SS        │ Dashboard                            │
│              │                                      │
│ Dashboard    │ Alumni        Attendance              │
│ Alumni       │  —             —                     │
│ Contributions│                                      │
│ Volunteers   │ Contributions   Pending              │
│ Activities   │  —              —                    │
│ Invitations  │                                      │
│              │ Recent records                       │
└──────────────┴──────────────────────────────────────┘
```

The dashboard can be denser than the public website.

---

# 28. Status Colors

Status should not rely on color alone.

Example:

```text
VERIFIED
PENDING
REJECTED
```

Use:

- Text
- Icons
- Borders
- Subtle color differences

Do not introduce a large unrelated color palette.

---

# 29. Volunteer Interface

Volunteer management belongs to the organizer side.

It should not be prominent on the alumni website.

Organizer interface:

```text
VOLUNTEERS

Name
Contact
Assigned Activity
Status
```

Activities:

```text
Registration
Catering
Venue
Photography
Technical
Coordination
```

The visual system remains consistent with the admin dashboard.

---

# 30. Future Invitation Interface

When invitation functionality is introduced:

```text
INVITATIONS

Audience
Message
Channel
Schedule
Preview
Send
```

Keep it functional and editorial.

Do not introduce a separate visual identity for invitations.

---

# 31. Responsive Design

## Desktop

Use:

- Wide editorial layouts
- Large photography
- Two-column compositions
- Strong section ribbons
- Generous whitespace

## Tablet

Collapse secondary columns while preserving hierarchy.

## Mobile

Use:

```text
Header
Hero
Image
Meet information
Story
Alumni
Contribution
Footer
```

The mobile version should preserve the visual language rather than simply stacking desktop cards.

---

# 32. Animation

Animation should be minimal.

Good:

- Section fade/reveal
- Image reveal
- Navigation transition
- Subtle hover movement
- Smooth scrolling

Avoid:

- Floating blobs
- Glowing elements
- Constant parallax
- 3D objects
- Cursor effects
- Large text animations

The website should look good with animation disabled.

---

# 33. Iconography

Use a consistent outline icon set such as:

```text
Lucide
```

or another restrained outline set.

Use icons only when they communicate meaning.

Do not use emoji as interface decoration.

---

# 34. Accessibility

Requirements:

- Semantic HTML
- Correct heading hierarchy
- Keyboard navigation
- Visible focus states
- Adequate contrast
- Form labels
- Alt text
- Reduced-motion support
- Status conveyed through text as well as color

The cream/navy/gold palette must be tested for accessible contrast.

---

# 35. Content Style

The writing should sound like an institution speaking to its alumni.

Prefer:

```text
The School welcomes its alumni back to campus.
```

over:

```text
Get ready for an unforgettable experience.
```

Prefer:

```text
Join fellow SC&SS alumni at the Alumni Meet 2026.
```

over:

```text
Let's make memories together.
```

The tone should be warm without becoming promotional.

---

# 36. Design Language Summary

The core visual vocabulary is:

```text
NAVY
████████████

CREAM
░░░░░░░░░░░░

GOLD
────────────

SERIF
Alumni Meet 2026

SANS
SCHOOL OF COMPUTER & SYSTEMS SCIENCES

PHOTOGRAPHY
Real SC&SS / JNU

MOTIF
Concentric circles / subtle geometry

STRUCTURE
Editorial grids + section ribbons + whitespace
```

---

# 37. What Makes This Different From a Generic AI Website

The following characteristics should be visible throughout the site:

1. **The SC&SS/JNU palette is the source of identity.**
2. **The placement brochure is the visual reference.**
3. **Real campus imagery carries emotional weight.**
4. **Typography does most of the visual work.**
5. **Gold is used as a restrained editorial accent.**
6. **The layout uses rules, ribbons, grids, and whitespace.**
7. **The interface does not depend on gradients or glassmorphism.**
8. **Content and institutional history drive the design.**
9. **The alumni community is represented through years, people, and stories.**
10. **The design should still look believable when all decorative effects are removed.**

---

# 38. Implementation Tokens

The CSS design tokens should start from:

```css
:root {
    --color-navy: #0B1F4D;
    --color-gold: #D4A745;
    --color-cream: #F7F3EA;
    --color-white: #FFFFFF;
    --color-text: #1A1A1A;
    --color-muted: #5A6478;

    --color-blue-2: #2E4D8B;
    --color-blue-3: #5B7BB8;
    --color-blue-4: #8FA8D4;

    --font-display: "Playfair Display", "Source Serif Pro", Georgia, serif;
    --font-body: "Inter", system-ui, sans-serif;
}
```

Spacing, radius, shadows, and type sizes should be centralized rather than scattered through individual components.

---

# 39. Design Decision Status

```text
Visual direction:
DECIDED

Reference:
SC&SS JNU Placement Brochure 2026–27

Primary color:
#0B1F4D Navy

Accent:
#D4A745 Gold

Background:
#F7F3EA Cream

Display font:
Playfair Display

Body/UI font:
Inter

Photography:
Real SC&SS/JNU imagery preferred

Contribution:
Google Form only in MVP

Public website:
Editorial / institutional

Admin:
Functional / information-dense
```

---

# 40. Design Change Rule

If a new visual pattern, color, typography decision, component, page, interaction pattern, or branding requirement is introduced, update this document.

Do not let important design decisions exist only in implementation code or chat history.

Before implementing a new page:

```text
Read PROJECT_INSTRUCTIONS.md
        ↓
Read this design.md
        ↓
Check architecture.md if routing/integration changes
        ↓
Check database_design.md if data changes
        ↓
Implement
        ↓
Update affected documentation
```

---

# 41. Final Direction

The website should feel like:

> **SC&SS JNU, brought onto the web for its alumni.**

Not:

> an alumni template customized with the SC&SS name.

The placement brochure already provides a strong institutional visual language. The website should preserve its navy, cream, gold, typography, photography, rules, grids, and editorial structure while adding the usability and responsiveness expected from a modern web application.
