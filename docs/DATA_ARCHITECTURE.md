# Data Architecture

## Core Principle

EduPredict serves data through an **AcademicDataProvider** abstraction — the application never depends on *where* academic data comes from. The active provider is chosen at runtime from the `data_sources` table (admin switchable from Settings → Data Sources).

## Data Sources

| Type | Name | Initial status | Description |
|---|---|---|---|
| `DEMO` | Demo Dataset | `ACTIVE` | Synthetic academic records generated locally for development and demos |
| `CSV` | Approved Academic Import | `AVAILABLE` | Academic records imported from an approved CSV export |
| `SAMVIDHA` | IARE Samvidha Integration | `NOT_CONFIGURED` | Official API integration; not configured unless official docs/credentials are provided |

Rules:

- Exactly **one** source is `ACTIVE` at any time; activating another demotes the previous to `AVAILABLE`.
- `NOT_CONFIGURED` sources **cannot** be activated (activation returns 400, `ProviderNotConfigured`).
- If no source is active, the app falls back to `DEMO` (see `get_active_data_source` in `backend/app/services/base.py`).

Switching source changes which **provider class** reads/derives student data; it does not delete data rows. See [Academic Provider](ACADEMIC_PROVIDER.md).

## Record Model

All providers read/write through the application database. Per-student granular record tables are the single source of truth for derived numbers (summary, analytics, risk):

| Table | Content |
|---|---|
| `academic_records` | subject-wise internal marks, assignment score, total, grade (one per subject/semester) |
| `attendances` | monthly attendance % per subject/semester |
| `engagements` | monthly LMS engagement score per semester |
| `assessments` | internal assessment marks (assessment 1/2) per subject/semester |
| `assignments` | assignment completion % / score per subject/semester |
| `predictions` | risk probability, level, model, feature contributions, recommendations |
| `interventions` | mentor meetings / counselling with status + impact timeline |
| `notifications` | early-warning and system notifications (per user) |

Reference data: `departments` (5, seeded), `sections` (per department A/B, per year/semester), `subjects` (4 per department, per semester), `semesters` (1–3, semester 1 current), `system_settings` (`risk_low`/`risk_high` thresholds).

## Seeded Data

`scripts/seed_database.py` (runs cleanly against an empty DB):

- **263 students / 269 users** — admin, 5 faculty (one per department), 260 bulk students, 2 demo students (`student01`, `student02`) plus 1 high-risk demo student (`student03`).
- Bulk students: usernames `student001`…`student260`, password `Student@123`; `student_id` scheme `f"{code}{2026-(i%3)}{i:03d}"` (e.g. `student001` → `CSE2026000`).
- Demo trio with hand-picked historical records so documented synthetic formula yields intuitive profiles:

| Username | Student ID | Risk | prob | Snapshot (perf / att / eng) |
|---|---|---|---|---|
| `student01` | `24951A05B1` | low | ≈0.03 | 92.1 / 93.7 / 85.6 |
| `student02` | `24951A05B2` | moderate | ≈0.41 | 63.3 / 76.6 / 61.2 |
| `student03` | `24951A05B3` | high | ≈0.9+ | 49.8 / 56.4 / 39.7 |

- Each demo student has historical predictions at small offsets around the current value (trend story), and interventions only where risk probability > 0.6.

## Faculty Scope (RBAC)

- **Admin** sees all 263 students.
- **Faculty** see only students in their department's sections (CSE faculty sees ~55).
- The scope applies to students list, analytics, interventions, predictions, and reports.

## Derived Numbers

`build_academic_summary(db, student, provider)` (`backend/app/services/base.py`) computes the personalized student dashboard from the student's own rows:

- `health` — averages of attendance %, overall score, engagement, internal 1/2 marks, assignment completion.
- `subjects` — per-subject attendance/internal/assignment/grade with up/down/stable trend.
- `risk` — from the student's **latest predicted** probability and level, plus current admin thresholds.
- `recommendations` — `generate_recommendations(features, risk_level, thresholds)`.
- `performance_history` — ordered (semester, label, score) from assessments + academic records.

Risk thresholds are **runtime-configurable** (`system_settings`), defaults `risk_low = 0.39`, `risk_high = 0.69`, with bounds validation on update (400 for invalid/out-of-order values).