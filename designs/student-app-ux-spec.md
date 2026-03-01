# Student Productivity & Task Management App — UX Design Spec

## Overview

Single-page app (one HTML file) served by FastAPI. Tab-based navigation, dark theme, card-based layout. Five views: Dashboard, Tasks, Study Sessions, Analytics, Pomodoro.

---

## Design Decisions (Resolved)

| Question | Decision | Rationale |
|---|---|---|
| Navigation pattern | **Top tab bar** (horizontal, sticky) | 5 views fit cleanly; sidebar wastes width on mobile |
| Analytics charts | **Pure CSS bars** (no canvas library) | No dependency, matches no-framework constraint |
| Pomodoro timer | **Circular countdown** (SVG stroke-dashoffset) | More visceral, student-friendly feel |
| Task create form | **Slide-in panel** (right side, 400px wide) | Keeps context visible; modal would obscure task list |

---

## Color Palette

```
Background layers:
  --bg-base:      #0d0f14   /* outermost page background */
  --bg-surface:   #161920   /* cards, panels, nav */
  --bg-elevated:  #1e2130   /* inputs, hovered cards, modals */
  --bg-overlay:   #252a3a   /* dropdowns, tooltips */

Accent / Brand:
  --accent:       #6c63ff   /* primary CTA, active tab underline */
  --accent-dim:   #4a43cc   /* hover state of accent */
  --accent-glow:  rgba(108,99,255,0.18)  /* focus ring, card hover shadow */

Priority colors:
  --priority-urgent: #ef4444   /* urgent badge bg */
  --priority-high:   #f97316   /* high badge bg */
  --priority-medium: #eab308   /* medium badge bg (dark text) */
  --priority-low:    #22c55e   /* low badge bg */

Status colors:
  --status-todo:       #64748b
  --status-in-progress:#6c63ff
  --status-done:       #22c55e
  --status-overdue:    #ef4444

Subject palette (10 rotating colors, user-assigned):
  --subj-0: #6c63ff   --subj-5: #f59e0b
  --subj-1: #06b6d4   --subj-6: #84cc16
  --subj-2: #ec4899   --subj-7: #14b8a6
  --subj-3: #f97316   --subj-8: #a78bfa
  --subj-4: #22c55e   --subj-9: #fb7185

Text:
  --text-primary:  #f1f5f9
  --text-secondary:#94a3b8
  --text-muted:    #475569
  --text-inverse:  #0d0f14   /* used on yellow/green badges */

Borders:
  --border:       rgba(255,255,255,0.07)
  --border-focus: #6c63ff

Danger:
  --danger:       #ef4444
  --danger-dim:   #b91c1c
```

---

## Typography

```
Font stack: 'Inter', 'Segoe UI', system-ui, sans-serif
            (Inter loaded from Google Fonts; fallback to system)

Scale:
  --text-xs:   0.70rem  / 400  — badge labels, helper text
  --text-sm:   0.80rem  / 400  — meta info, timestamps
  --text-base: 0.925rem / 400  — body, form labels
  --text-md:   1.05rem  / 500  — card titles, list items
  --text-lg:   1.25rem  / 600  — section headings, panel headers
  --text-xl:   1.6rem   / 700  — stat numbers, timer display
  --text-2xl:  2.2rem   / 700  — dashboard big numbers
  --text-3xl:  3.5rem   / 700  — pomodoro countdown

Line height: 1.5 body / 1.2 headings
Letter spacing: 0.04em on xs/sm uppercase labels
```

---

## Spacing & Shape

```
Spacing unit: 4px base (0.25rem)
  Common tokens: 4 / 8 / 12 / 16 / 20 / 24 / 32 / 48px

Border radius:
  --radius-sm:  6px    — badges, tags, inputs
  --radius-md:  10px   — cards, dropdowns
  --radius-lg:  16px   — panels, modals
  --radius-xl:  24px   — pomodoro circle container
  --radius-full: 999px — pill badges, avatar circles

Shadows:
  --shadow-card:  0 2px 8px rgba(0,0,0,0.35)
  --shadow-panel: 0 8px 32px rgba(0,0,0,0.55)
  --shadow-focus: 0 0 0 3px var(--accent-glow)
```

---

## CSS Class Naming Convention

**Prefix:** `sp-` (Student Productivity)  
**Pattern:** BEM-lite — `sp-[block]__[element]--[modifier]`

```
Examples:
  sp-card               — base card container
  sp-card--elevated     — hover/active card state
  sp-badge              — base badge
  sp-badge--urgent      — priority modifier
  sp-badge--done        — status modifier
  sp-btn                — base button
  sp-btn--primary       — accent CTA
  sp-btn--ghost         — outline/ghost
  sp-btn--danger        — destructive action
  sp-input              — text input / select
  sp-tab                — nav tab item
  sp-tab--active        — active tab
  sp-panel              — slide-in side panel
  sp-panel--open        — panel visible state
  sp-stat               — dashboard stat card
  sp-task-card          — task list item card
  sp-session-row        — study session list row
  sp-bar                — CSS progress bar container
  sp-bar__fill          — the colored fill element
  sp-timer              — pomodoro circle wrapper
  sp-overlay            — dark backdrop for panel
```

---

## Responsive Breakpoints

```
Mobile:  375px–767px   (sm)
Tablet:  768px–1023px  (md)
Desktop: 1024px–1440px (lg)

Layout shifts:
  Nav:         top tab bar (all sizes) — tabs shrink to icon+short-label on mobile
  Dashboard:   4-col stat row → 2×2 grid → 2×2 grid (stays 2×2 on mobile)
  Task list:   sidebar filters + card list → full-width stacked
  Side panel:  400px slide-in → full-width bottom sheet on mobile
  Analytics:   2-col grid → single column
  Study log:   side-by-side form+list → stacked
  Pomodoro:    centered, no layout change needed
```

---

## Navigation — Top Tab Bar

```
┌────────────────────────────────────────────────────────────────────────────┐
│  📚 StudyFlow                                              [🌙] [⚙️]       │
├────────────────────────────────────────────────────────────────────────────┤
│  [Dashboard]  [Tasks]  [Study Sessions]  [Analytics]  [Pomodoro 🍅]        │
│  ────────                                                                  │
└────────────────────────────────────────────────────────────────────────────┘

Specs:
  - Height: 56px header + 48px tab row = 104px total sticky nav
  - Tab bar background: var(--bg-surface)
  - Border-bottom: 1px solid var(--border)
  - Active tab: bottom border 2px solid var(--accent), text color var(--accent)
  - Inactive tab: text color var(--text-secondary), hover → var(--text-primary)
  - Pomodoro tab: shows 🍅 emoji + "Pomodoro" label; when timer running, shows
    pulsing red dot indicator next to label
  - Mobile: all 5 tabs fit by abbreviating labels:
      Dashboard → Home, Study Sessions → Sessions, Analytics → Stats
  - Transition: tab underline slides (transform: translateX) with 200ms ease
```

---

## View 1: Dashboard

### User Flow
```
App loads → Dashboard is default view
  → Stats cards render (API: GET /analytics/summary)
  → Recent tasks render (API: GET /tasks?limit=5&sort=created_at)
  → Streak data renders (from summary response)
  → [+ New Task] button → slide-in panel opens
```

### Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│  NAV BAR (sticky, 104px)                                                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Good morning, Student 👋          [+ New Task]                            │
│  Monday, 14 July 2025                                                      │
│                                                                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │
│  │  Total Tasks │ │  Completed   │ │   Pending    │ │   Overdue    │     │
│  │     24       │ │     18       │ │      4       │ │      2       │     │
│  │  (neutral)   │ │  (green)     │ │  (accent)    │ │  (red)       │     │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘     │
│                                                                            │
│  ┌─────────────────────────────────┐  ┌────────────────────────────────┐  │
│  │  🔥 Streak                      │  │  📅 Today's Focus              │  │
│  │  Current: 7 days                │  │  Study time today: 2h 30m      │  │
│  │  Longest: 14 days               │  │  Pomodoros today: 6            │  │
│  │  ■■■■■■■□□□□□□□  (7/14 bar)    │  │  [Start Pomodoro →]            │  │
│  └─────────────────────────────────┘  └────────────────────────────────┘  │
│                                                                            │
│  Recent Tasks                              [View All Tasks →]              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ● Fix lab report      [URGENT] [Study]  Due: Today    ⚠ Overdue   │  │
│  │  ● Read ch 4–6         [HIGH]   [Study]  Due: Wed                  │  │
│  │  ● Group project mtg   [MED]    [Project] Due: Thu                 │  │
│  │  ● Buy stationery      [LOW]    [Personal] Due: Fri                │  │
│  │  ✓ Submit assignment   [HIGH]   [Exam]    Done                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Stat Card Spec

```
Size:        flex 1, min-width 140px, height 96px
Background:  var(--bg-surface)
Border:      1px solid var(--border)
Border-radius: var(--radius-md)
Padding:     16px
Shadow:      var(--shadow-card)

Label:   --text-sm, var(--text-secondary), uppercase, letter-spacing 0.06em
Number:  --text-2xl, var(--text-primary), font-weight 700
Color accents (left border 3px):
  Total:     var(--accent)
  Completed: var(--status-done)
  Pending:   var(--status-in-progress)
  Overdue:   var(--status-overdue)

Hover: background → var(--bg-elevated), shadow expands slightly, 150ms ease
```

### Streak Widget Spec

```
Background:  var(--bg-surface)
Left accent: 3px solid #f97316 (fire orange)
Icon:        🔥 emoji, 1.4rem
Progress bar: full-width, 6px height, radius-full
  Fill = (current/longest)*100%
  Fill color: linear-gradient(90deg, #f97316, #ef4444)
  Track color: var(--bg-overlay)
```

### Recent Tasks (Dashboard)

```
Each row:
  ● / ✓  [title 200px flex]  [priority badge]  [category badge]  [due date text]  [status pill]
  
  Overdue indicator: small ⚠️ icon + due date text in var(--danger)
  Done rows: title in var(--text-muted) + text-decoration: line-through, opacity 0.65
  Row height: 44px, border-bottom: 1px solid var(--border)
  Hover: background var(--bg-elevated)
  Not clickable (dashboard is read-only — no expand in v1)
```

---

## View 2: Tasks

### User Flow
```
Tasks tab → Task list loads (GET /tasks)
  → Filters applied (status/priority/category/search) → list re-fetches / client-side filter
  → [+ New Task] → slide-in panel opens → form filled → [Save] → POST /tasks → panel closes → list refreshes
  → Task card [✓ Complete] → PATCH /tasks/{id}/complete → card updates in-place
  → Task card [🗑] → confirm inline → DELETE /tasks/{id} → card fades out
  → Task card [▶ expand] → subtasks section reveals (accordion)
```

### Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│  NAV BAR                                                                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Tasks (24)                                          [+ New Task]          │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Status [All ▾]  Priority [All ▾]  Category [All ▾]  [🔍 Search…]   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  [URGENT] Fix lab report                          ⚠ Due: Today      │  │
│  │  ────────────────────────────────────────────────────────────────── │  │
│  │  📚 Study  •  Physics  •  No subtasks             [✓ Done] [🗑] [▶] │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  [HIGH] Read chapters 4–6                         Due: Wed 16 Jul   │  │
│  │  ────────────────────────────────────────────────────────────────── │  │
│  │  📚 Study  •  Mathematics  •  2 subtasks          [✓ Done] [🗑] [▶] │  │
│  │  ▼ Subtasks                                                         │  │
│  │    ☐ Chapter 4 — complete                                           │  │
│  │    ☑ Chapter 5 — notes done                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  [LOW] Buy stationery                             Due: Fri 18 Jul   │  │
│  │  ────────────────────────────────────────────────────────────────── │  │
│  │  🙂 Personal  •  No subject                       [✓ Done] [🗑] [▶] │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Task Card Spec

```
Container:
  Background:    var(--bg-surface)
  Border:        1px solid var(--border)
  Border-radius: var(--radius-md)
  Padding:       14px 16px
  Margin-bottom: 8px
  Left border:   4px solid [priority color]  ← replaces left border-radius
  Transition:    border-color 150ms ease, box-shadow 150ms ease

Row 1: [priority badge]  [title — --text-md, var(--text-primary)]  [due date]
Row 2: [category icon+label]  [subject dot+name]  [subtask count]  [action buttons]

Overdue state:
  Left border: var(--danger)
  Due date: var(--danger), font-weight 600, prepended with ⚠

Done state:
  Left border: var(--status-done)
  Title: text-decoration line-through, color var(--text-muted)
  Opacity: 0.72
  [✓ Done] button: disabled, label changes to "Completed"

Hover state (not done):
  Background: var(--bg-elevated)
  Box-shadow: var(--shadow-card)
```

### Priority Badge Spec

```
Shape:    pill, padding 2px 8px, border-radius var(--radius-full)
Font:     --text-xs, font-weight 600, uppercase, letter-spacing 0.05em

URGENT: bg #ef4444, color #fff
HIGH:   bg #f97316, color #fff
MEDIUM: bg #eab308, color #0d0f14   ← dark text for contrast on yellow
LOW:    bg #22c55e, color #0d0f14   ← dark text for contrast on green
```

### Filter Bar Spec

```
Container: bg var(--bg-surface), border-bottom 1px solid var(--border),
           padding 12px 16px, sticky below nav
Layout: flex row, gap 8px, flex-wrap wrap

Dropdowns (sp-input):
  Background: var(--bg-elevated)
  Border: 1px solid var(--border)
  Color: var(--text-primary)
  Height: 36px, padding: 0 12px, border-radius var(--radius-sm)
  Arrow: custom chevron SVG, right: 10px

Search input:
  flex: 1, min-width: 160px
  Placeholder: "Search tasks…" in var(--text-muted)
  Left icon: 🔍 (16px, var(--text-muted))
  On focus: border-color var(--accent), box-shadow var(--shadow-focus)
```

### Create / Edit Task — Slide-In Panel

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  [dim overlay]                                    ┌────────────────────────────┐  │
│                                                   │  New Task              [×] │  │
│                                                   ├────────────────────────────┤  │
│                                                   │  Title *                   │  │
│                                                   │  [________________________]│  │
│                                                   │                            │  │
│                                                   │  Description               │  │
│                                                   │  [________________________]│  │
│                                                   │  [________________________]│  │
│                                                   │                            │  │
│                                                   │  Priority *    Category *  │  │
│                                                   │  [Urgent ▾]    [Study ▾]  │  │
│                                                   │                            │  │
│                                                   │  Due Date       Subject    │  │
│                                                   │  [📅 ________] [None  ▾]  │  │
│                                                   │                            │  │
│                                                   │  Tags (comma-separated)    │  │
│                                                   │  [________________________]│  │
│                                                   │                            │  │
│                                                   │  Subtasks                  │  │
│                                                   │  [________________________]│  │
│                                                   │  [+ Add subtask]           │  │
│                                                   │                            │  │
│                                                   ├────────────────────────────┤  │
│                                                   │  [Cancel]    [Save Task]   │  │
│                                                   └────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Panel Specs:**
```
Width (desktop):  400px, fixed right edge, full viewport height
Width (mobile):   100vw, slides up from bottom (bottom sheet), max-height 90vh
Background:       var(--bg-surface)
Border-left:      1px solid var(--border) (desktop) / border-top (mobile)
Shadow:           var(--shadow-panel)

Open animation:
  Desktop: translateX(400px) → translateX(0), 280ms cubic-bezier(0.4,0,0.2,1)
  Mobile:  translateY(100%) → translateY(0), 280ms same easing

Overlay:  rgba(0,0,0,0.55), fades in 200ms
Close:    click overlay OR [×] button OR [Cancel] button
          → reverse animation, overlay fades out

Scroll: panel body scrolls independently (overflow-y: auto)
Footer (Cancel + Save): sticky at panel bottom, bg var(--bg-surface),
        border-top 1px solid var(--border), padding 12px 16px

Form fields:
  All sp-input: height 40px (textarea: auto), padding 10px 12px
  border-radius: var(--radius-sm), border: 1px solid var(--border)
  background: var(--bg-elevated), color: var(--text-primary)
  On focus: border-color var(--accent), box-shadow var(--shadow-focus)

Required (*) fields: label has asterisk in var(--danger)
Validation error: red border + small error text below field, var(--danger), --text-xs
  Error appears on blur OR on failed submit attempt

[Save Task] button:
  sp-btn sp-btn--primary
  background: var(--accent), color #fff, height 40px, border-radius var(--radius-sm)
  Disabled when: title is empty OR priority not selected OR category not selected
  Loading state: spinner icon replaces label text, button stays disabled

[Cancel] button: sp-btn sp-btn--ghost, border 1px solid var(--border)

Subtask rows:
  Each row: [☐ checkbox] [text input, flex-1] [× remove]
  [+ Add subtask]: ghost button, full width, dashed border
```

---

## View 3: Study Sessions

### User Flow
```
Sessions tab → Load sessions (GET /study-sessions)
  → [Log Session] form visible at top
  → Fill subject, duration, notes → [Save] → POST /study-sessions → list refreshes
  → Session in list: [🗑 Delete] → DELETE /study-sessions/{id} → row fades out
  → Summary stats recalculate from list data (client-side)
```

### Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│  NAV BAR                                                                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Study Sessions                                                            │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Log New Session                                                     │  │
│  │  Subject [Select Subject ▾]   Duration [___] min   [Save Session]   │  │
│  │  Notes   [optional notes_______________]                             │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌─────────────────────────────────┐  ┌────────────────────────────────┐  │
│  │  Total Study Time               │  │  By Subject                    │  │
│  │  12h 45m                        │  │  Physics    ████████░░  3h 20m │  │
│  │  This week: 4h 30m              │  │  Math       ██████░░░░  2h 40m │  │
│  │                                 │  │  English    ████░░░░░░  1h 50m │  │
│  └─────────────────────────────────┘  └────────────────────────────────┘  │
│                                                                            │
│  Sessions (34)                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ● Physics                  2h 0m     Today, 14:30          [🗑]    │  │
│  │    "Reviewed thermodynamics chapter"                                 │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │  ● Mathematics              1h 20m    Today, 11:00          [🗑]    │  │
│  │    "Practice integrals"                                              │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │  ● English                  45m       Yesterday, 20:00      [🗑]    │  │
│  │    —                                                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Log Session Form Spec

```
Container: sp-card, padding 16px
Layout (desktop): flex row, gap 12px, align-items flex-end
Layout (mobile): stacked, each field full-width

Fields:
  Subject:  sp-input select, width 180px (desktop) / full (mobile)
            Shows subject name with color dot prefix
  Duration: sp-input number, width 100px, placeholder "60", suffix label "min"
  Notes:    sp-input text, flex 1, placeholder "Optional notes…"
  [Save Session]: sp-btn sp-btn--primary, height 40px, min-width 120px
                  Disabled when: subject not selected OR duration ≤ 0

Inline validation: duration must be 1–480 (8 hours max)
Error: small text below field in var(--danger)
```

### Subject Bar Chart Spec

```
Container: sp-card, padding 16px
Each bar row:
  [●colored dot] [subject name, 100px, truncated]  [bar track flex-1]  [time label]

Bar track: height 8px, border-radius var(--radius-full), bg var(--bg-overlay)
Bar fill:  height 8px, border-radius var(--radius-full), bg = subject color (--subj-N)
           Width = (subject_hours / max_subject_hours) * 100%
           Transition: width 600ms cubic-bezier(0.4,0,0.2,1) on mount/update

Row height: 36px, gap 8px between rows
Max 10 subjects shown; if more, show "and N more…" in --text-muted
```

### Session Row Spec

```
Border-bottom: 1px solid var(--border)
Padding: 12px 16px
Left colored dot: 8px circle, subject color (--subj-N)

Line 1: [colored subject name]  [duration in bold]  [timestamp right-aligned]  [🗑 button]
Line 2: [notes in --text-secondary --text-sm, italic] OR hidden if no notes
Duration format: "2h 0m" for ≥60min, "45m" for <60min
Timestamp: relative ("Today, 14:30" / "Yesterday, 20:00" / "Mon, 14:30")
[🗑] delete: sp-btn--ghost, icon only, shows on hover (desktop) / always visible (mobile)
  Click → inline confirm: button turns red, label "Confirm?" for 3s → click again to delete
  If not confirmed in 3s: revert to normal state
```

---

## View 4: Analytics

### User Flow
```
Analytics tab → Load analytics (GET /analytics/summary + GET /tasks + GET /study-sessions)
  → All panels render with live data
  → No user interactions (read-only view)
```

### Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│  NAV BAR                                                                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Analytics                                                                 │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  Task Completion Rate                                              │    │
│  │  75%  ████████████████████░░░░░░░░  18 of 24 tasks complete       │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│  ┌─────────────────────────────────┐  ┌────────────────────────────────┐  │
│  │  By Category                    │  │  By Priority                   │  │
│  │  Study    ████████░░  12 tasks  │  │  Urgent   ██░░░░░░  3 tasks   │  │
│  │  Project  █████░░░░   7 tasks   │  │  High     █████░░░  7 tasks   │  │
│  │  Exam     ██░░░░░░░   3 tasks   │  │  Medium   ████████  11 tasks  │  │
│  │  Personal █░░░░░░░░   2 tasks   │  │  Low      ██░░░░░░  3 tasks   │  │
│  └─────────────────────────────────┘  └────────────────────────────────┘  │
│                                                                            │
│  ┌─────────────────────────────────┐  ┌────────────────────────────────┐  │
│  │  Study Hours by Subject         │  │  Streak & Productivity         │  │
│  │  Physics  ████████░░  3h 20m    │  │  🔥 Current streak: 7 days    │  │
│  │  Math     ██████░░░░  2h 40m    │  │  🏆 Longest streak: 14 days   │  │
│  │  English  ████░░░░░░  1h 50m    │  │  📅 Overdue tasks: 2          │  │
│  │                                 │  │  ⏱  Total study: 12h 45m      │  │
│  └─────────────────────────────────┘  └────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Completion Rate Bar Spec

```
Container: sp-card, full width, padding 20px 24px
Layout: flex row, align-items center, gap 24px

Percentage:
  --text-xl, font-weight 700, color var(--accent), min-width 56px

Progress bar:
  flex: 1, height 14px, border-radius var(--radius-full)
  Track: var(--bg-overlay)
  Fill: linear-gradient(90deg, var(--accent), #06b6d4)
  Width: {completion_rate}% (animated on load: 0→N%, 800ms ease-out)

Description: "18 of 24 tasks complete", --text-sm, var(--text-secondary)
```

### Category / Priority Bar Chart Spec

```
Container: sp-card, padding 16px
Grid: 2 cards side by side (desktop) / stacked (mobile)

Category bar colors:
  study:    var(--accent)   #6c63ff
  project:  #06b6d4
  exam:     #ef4444
  personal: #22c55e

Priority bar colors:
  urgent: #ef4444
  high:   #f97316
  medium: #eab308
  low:    #22c55e

Each row: [label 80px] [bar track flex-1] [count, right-aligned, --text-sm]
Bar height: 10px, border-radius var(--radius-full)
Bar fill width: (count / max_count) * 100%, animated 600ms ease-out on load
Row gap: 12px
```

---

## View 5: Pomodoro

### User Flow
```
Pomodoro tab → Timer view loads
  → Timer shows 25:00 (default), paused state
  → [Select Task] dropdown optional
  → [Start] → countdown begins, [Start] becomes [Pause]
  → [Pause] → countdown pauses, [Pause] becomes [Resume]
  → Timer reaches 00:00 → auto-fires "complete" → POST /pomodoro-sessions
     → Success animation → stats update → timer resets to 25:00
  → [Complete] at any time → same POST flow, counts partial session
  → [Reset] → confirms, resets to 25:00, no session logged
```

### Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│  NAV BAR                                                                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                         Pomodoro Timer  🍅                                 │
│                                                                            │
│                  ┌────────────────────────────────┐                        │
│                  │   Linked Task (optional)        │                        │
│                  │   [Select a task… ▾]            │                        │
│                  └────────────────────────────────┘                        │
│                                                                            │
│                       ╭──────────────────────╮                            │
│                      ╱  ·  ·  ·  ·  ·  ·  ·  ╲                           │
│                     │   ·                   ·  │                           │
│                     │   ·    25:00          ·  │   ← SVG circle            │
│                     │   ·   Focus time      ·  │                           │
│                     │   ·                   ·  │                           │
│                      ╲  ·  ·  ·  ·  ·  ·  ·  ╱                           │
│                       ╰──────────────────────╯                            │
│                                                                            │
│                     [    Start    ]   [Reset]                              │
│                                                                            │
│                         ─────────────────────                              │
│                                                                            │
│                  🍅 Today: 6 pomodoros                                     │
│                  ⏱  Total focus today: 150 min                            │
│                  📋 Linked: Fix lab report                                 │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Circular Timer Spec

```
Implementation: SVG circle + stroke-dashoffset animation

Outer container (sp-timer):
  width: 240px, height: 240px, margin: 0 auto
  border-radius: var(--radius-xl)

SVG:
  viewBox: "0 0 200 200", width: 100%, height: 100%

Track circle:
  cx: 100, cy: 100, r: 90
  stroke: var(--bg-overlay), stroke-width: 8
  fill: none

Progress circle:
  cx: 100, cy: 100, r: 90
  stroke-dasharray: 565.49 (2π × 90 = circumference)
  stroke-dashoffset: computed = circumference × (1 - elapsed/total)
  stroke: var(--accent)  → when running
          var(--danger)  → when in last 60 seconds (< 1 min remaining)
          #22c55e        → completed flash state
  stroke-width: 8
  stroke-linecap: round
  fill: none
  transform: rotate(-90deg), transform-origin: center
  transition: stroke-dashoffset 1s linear (every second tick)
              stroke 300ms ease (color change)

Center text (absolute, centered over SVG):
  Time display: --text-3xl (3.5rem), font-weight 700, var(--text-primary)
  Sub-label:    --text-sm, var(--text-muted)  — "Focus time" / "Paused" / "Break time"

States:
  idle:    accent stroke, "Focus time" label, 100% filled arc
  running: stroke animates, countdown visible, label "Focus time"
  paused:  stroke stops, label "Paused", slight pulse on center text
  warning: last 60s → stroke turns var(--danger), center text turns var(--danger)
  done:    arc fills green briefly (500ms), center shows "Done! 🎉", then resets
```

### Timer Buttons Spec

```
Layout: flex row, gap 12px, justify-content center

[Start] / [Pause] / [Resume]:
  sp-btn sp-btn--primary
  Width: 140px, height: 48px, border-radius: var(--radius-md)
  font-size: --text-md, font-weight: 600
  Running state label: "Pause"
  Paused state label: "Resume"

[Complete]:
  sp-btn sp-btn--ghost with green border (var(--status-done))
  Width: 120px, height: 40px
  Visible only when timer is running or paused (not in idle state)
  Click → immediately logs session → success flash

[Reset]:
  sp-btn sp-btn--ghost
  Width: 80px, height: 40px
  When timer is idle: disabled (nothing to reset)
  When running/paused: enabled — click shows inline confirm "Reset?" for 3s
```

### Today's Stats Row Spec

```
Container: centered, max-width 320px, margin-top 32px
Three rows, each: icon + label, --text-base, var(--text-secondary)
Numbers: var(--text-primary), font-weight 600
Linked task row: only shown when a task is selected from dropdown
  Shows task title truncated to 30 chars, with priority badge
```

---

## Interaction Notes (Global)

### Loading States
```
Initial page load:
  Each view shows skeleton cards — same dimensions as real cards,
  animated shimmer: linear-gradient moving left-to-right, 1.5s loop
  background: linear-gradient(90deg, var(--bg-surface) 25%, var(--bg-elevated) 50%, var(--bg-surface) 75%)
  background-size: 200% 100%
  animation: shimmer 1.5s infinite

API calls (not initial):
  Buttons show spinner (SVG rotating circle) instead of label text
  Button stays at same width (min-width set) to prevent layout shift
  Other content remains visible (no full-screen loader)
```

### Empty States
```
Task list — no tasks at all:
  Centered illustration area (emoji: 📋), --text-lg "No tasks yet"
  --text-sm --text-muted "Create your first task to get started"
  [+ New Task] button below

Task list — filters return nothing:
  Centered 🔍 emoji, "No tasks match your filters"
  [Clear Filters] ghost button

Study sessions — none logged:
  Centered 📚 emoji, "No sessions logged yet"
  "Log your first study session above"

Analytics — no data:
  Show all panels with 0 values (bars at 0%, "0h 0m", etc.)
  Do NOT show empty state — zero-data analytics is still valid info
```

### Error States
```
API error (load failure):
  Inline error banner inside the view content area (not a modal)
  Background: rgba(239,68,68,0.1), border-left 3px solid var(--danger)
  Icon: ⚠️, message: "Failed to load [resource]. [Retry]"
  [Retry] is a text link that re-fires the request

Form submission error:
  Field-level: red border + error text below field (--text-xs, var(--danger))
  General error: red banner at top of form/panel

Delete errors: inline text "Delete failed. Try again." replaces button, auto-clears 3s
```

### Success Feedback
```
Session saved:     form clears + brief green flash on form border (300ms) + list item slides in from top
Task created:      panel closes + new card slides in at top of list (300ms translateY + opacity)
Task completed:    card border turns green, title gets strikethrough, opacity drops — in-place, no reload
Task deleted:      card fades out + collapses height (200ms)
Pomodoro complete: timer circle flashes green, center text "Done! 🎉" for 1.5s, then resets
```

### Hover & Focus
```
All interactive elements: cursor pointer
Focus ring: box-shadow var(--shadow-focus) on all focusable elements (inputs, buttons, tabs)
No outline: outline: none; — replaced entirely by box-shadow focus ring
Cards (non-clickable): hover raises box-shadow only
Cards (clickable): hover raises + slight translateY(-1px), 150ms ease
Buttons: hover darkens bg by ~12% (use filter: brightness(0.88))
Tab labels: 200ms color transition
```

### Animations Summary
```
Tab switch:        view fades out (opacity 0, 150ms) then new view fades in (150ms)
Panel open:        translateX / translateY, 280ms cubic-bezier(0.4,0,0.2,1)
Panel close:       reverse, 200ms ease
Card enter:        translateY(-8px) + opacity 0 → natural, 250ms ease-out
Card exit:         opacity → 0 + height → 0 + margin → 0, 200ms ease-in
Bar chart fill:    0 → N%, 600ms ease-out, triggered on tab enter (IntersectionObserver)
Pomodoro tick:     stroke-dashoffset transition 1s linear
Shimmer skeleton:  1.5s infinite linear
```

---

## Component Summary Table

| Component | States | Behavior |
|---|---|---|
| sp-tab | default, hover, active | color transition 200ms; active = accent color + bottom border |
| sp-stat | default, hover | hover raises shadow; number animates count-up on load |
| sp-task-card | default, hover, done, overdue | left border color indicates priority/state; done = strikethrough |
| sp-badge--priority | urgent, high, medium, low | pill shape, static color per priority |
| sp-badge--status | todo, in-progress, done, overdue | pill shape, static color per status |
| sp-btn--primary | default, hover, disabled, loading | accent bg; loading = spinner; disabled = opacity 0.45 |
| sp-btn--ghost | default, hover, disabled | border + transparent bg; hover = bg var(--bg-elevated) |
| sp-btn--danger | default, hover | red bg; used only for destructive confirms |
| sp-input | default, focus, error, disabled | focus = accent border + glow; error = red border |
| sp-panel | closed, open | slide animation; scroll independently; sticky footer |
| sp-overlay | hidden, visible | opacity 0→0.55 on panel open; click closes panel |
| sp-timer | idle, running, paused, warning, done | SVG stroke changes; text changes; color shifts at <60s |
| sp-bar | static | fill animates once on view enter; CSS only |
| sp-session-row | default, hover, delete-confirm | delete btn visible on hover; confirm state turns red |

---

## Resolved Questions

- [x] **Subjects management** — **Inline only for v1.** A dedicated "Subjects" tab is included (6th tab) with create/list/delete. Subjects also appear as dropdowns in the task and session forms. No separate settings panel.
- [x] **Subtask completion** — **Manual only.** Checking all subtasks does NOT auto-advance the parent task to "done." User must click [✓ Done] on the parent task explicitly.

---

## View 6: Subjects

### User Flow
```
Subjects tab → Load subjects (GET /subjects)
  → Subject list renders
  → [+ New Subject] inline form → enter name → [Save] → POST /subjects → list refreshes
  → Subject card [🗑 Delete] → inline confirm → DELETE /subjects/{id} → card fades out
```

### Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│  NAV BAR (now 6 tabs: Dashboard | Tasks | Sessions | Analytics | Pomodoro 🍅 | Subjects) │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Subjects                                                                  │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Add Subject                                                         │  │
│  │  Name [______________________________]  [+ Add Subject]             │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  Your Subjects (5)                                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ● Physics                                                   [🗑]    │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │  ● Mathematics                                               [🗑]    │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │  ● English                                                   [🗑]    │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │  ● Chemistry                                                 [🗑]    │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │  ● History                                                   [🗑]    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Add Subject Form Spec

```
Container: sp-card, padding 16px
Layout: flex row, gap 12px, align-items center

Name input:
  sp-input, flex: 1, placeholder "Subject name…"
  Max length: 60 characters
  On focus: accent border + glow
  Error (empty submit): red border + "Name is required" below field

[+ Add Subject] button:
  sp-btn sp-btn--primary, min-width 140px, height 40px
  Disabled when: input is empty
  Loading state: spinner replaces label
  On success: input clears, new subject slides into list from top
```

### Subject List Item Spec

```
Container: border-bottom 1px solid var(--border), padding 12px 16px
Layout: flex row, align-items center

Color dot:
  8px circle, color = var(--subj-N) where N = (subject_index % 10)
  margin-right: 10px

Subject name:
  --text-md, var(--text-primary), flex: 1

[🗑] Delete button:
  sp-btn--ghost, icon only, 32px × 32px
  Visible on hover (desktop) / always visible (mobile)
  Click → inline confirm: button turns red + label "Confirm?" for 3s
  Second click within 3s → DELETE /subjects/{id} → row fades out
  No confirm → reverts to icon state

Empty state (no subjects):
  Centered 🏷️ emoji, --text-lg "No subjects yet"
  --text-sm --text-muted "Add subjects to organize your tasks and sessions"
```

### Navigation Update

```
The top tab bar now has 6 tabs:
  [Dashboard] [Tasks] [Sessions] [Analytics] [Pomodoro 🍅] [Subjects]

Mobile abbreviation:
  Dashboard → Home
  Sessions  → Sessions  (unchanged — fits)
  Analytics → Stats
  Subjects  → Subjects  (unchanged — fits)

On very narrow screens (< 400px), all 6 tabs compress uniformly.
Tab bar may scroll horizontally if labels overflow — no wrapping.
Tab strip scroll: overflow-x: auto, scrollbar-width: none (hidden scrollbar).
```

---

*Spec version: 1.1 — Thread cea80422 — Open questions resolved by EM*
