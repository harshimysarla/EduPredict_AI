# Demo Guide

A 15-minute walkthrough of EduPredict AI with seeded data.

## Prerequisites

Backend on `http://127.0.0.1:8000`, frontend on `http://localhost:5173` (see root README for setup), database seeded with `python scripts/seed_database.py`.

## 1. Log In (Admin)

Go to http://localhost:5173 → **Log in** with `admin@edupredict.local` / `Admin@123`.

- **Settings** (sidebar) — departments, sections, subjects, faculty are pre-seeded. Create a new department, section, or subject to see admin CRUD. Create a faculty account to see instant login.
- **Dashboard** — KPIs: total students, at-risk counts, intervention coverage, average risk.

## 2. Faculty View

Log out, log in as `faculty@edupredict.local` / `Faculty@123`.

- **Students** — search (e.g. "Sanjay"), filter by department/risk, sort by risk probability. Open any student.
- **Student profile** — four tabs:
  - Overview: current risk badge, trend chart, key stats
  - Performance/Attendance/Engagement: per-semester charts
  - Run **New Prediction** — adjust feature sliders (e.g. drop attendance to ~45 and internal marks to ~40) → see the risk jump to HIGH, per-factor explanation, and tailored recommendations.
- **Predictions** — full history for every student, newest first.
- **Analytics** — risk distribution, attendance↔performance correlation, score distributions, and intervention impact (compare risk before/after an intervention).
- **Interventions** — create a mentor meeting for an at-risk student, set status to in_progress, then completed (completed_date stamps automatically).

## 3. Model Lab

- **Dataset** — upload `data/student_performance.csv` (600 rows). Validate → green report. Train → both models appear with metrics.
- **Models** — see versioned list; the newest training run's best model is active. Open a version for the confusion matrix and feature importance (attendance should dominate). Activate any older version to switch the production model — then re-run a prediction and watch it use the activated model.

## 4. Early Warning

In **Students**, open a student currently LOW risk, run a prediction with poor inputs → risk escalates to HIGH. The bell in the top bar shows a new **prediction_alert** notification; faculty dashboards reflect the change.

## 5. Student View

Log in as `student@edupredict.local` / `Student@123`.

- Personal dashboard: own risk level, trend, attendance/engagement stats, and recommendations.
- Student role cannot see other students (try `/students` in a new tab → 403).

## 6. Reports

As faculty, open **Reports**, pick a student → preview the JSON report, then download CSV.

## 7. Sanity Checks

- Refresh tokens work across the app (JWT in localStorage, 60 min expiry).
- Dark mode toggle in the top bar persists.
- Notification bell supports mark-all-read.
- Global search finds students by name/id.

## Resetting the Demo

```bash
python -c "from sqlalchemy import text; from app.core.database import SessionLocal
with SessionLocal() as db:
    for t in ['notifications','interventions','predictions','engagement_records','attendance_records','academic_records','students','faculty_profiles','sections','subjects','departments','users','model_versions','datasets']:
        db.execute(text(f'TRUNCATE TABLE {t} CASCADE'))
    db.commit()"
python scripts/seed_database.py
```

(Adjust sys.path — run from repo root.)
