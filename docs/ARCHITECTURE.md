# Architecture

## Overview

EduPredict AI is a full-stack application with three layers:

```
┌─────────────────────┐     /api (proxied by Vite)     ┌──────────────────────┐
│  React SPA          │ ─────────────────────────────► │  FastAPI (uvicorn)   │
│  Vite dev server    │ ◄───────────────────────────── │  port 8000           │
│  http://localhost:5173                                │                      │
└─────────────────────┘                                 │  ├─ REST routers      │
        JWT stored in localStorage                      │  ├─ services layer    │
        (`edupredict_token`)                            │  └─ ML pipeline       │
                                                        └──────────┬───────────┘
                                                                   │ SQLAlchemy
                                                        ┌──────────▼───────────┐
                                                        │  PostgreSQL 16       │
                                                        │  db: edupredict      │
                                                        └──────────────────────┘
```

## Backend

### Layering

| Layer | Path | Responsibility |
|---|---|---|
| API routers | `backend/app/api/` | HTTP handling, auth, validation, RBAC |
| Services | `backend/app/services/` | Business logic, ML orchestration, notifications |
| ML pipeline | `backend/app/ml/` | Data generation, training, model persistence, prediction, explanation |
| Models | `backend/app/models/` | SQLAlchemy ORM models |
| Schemas | `backend/app/schemas/` | Pydantic request/response models |
| Core | `backend/app/core/` | Settings, engine/session, security, dependency injection |

### Request flow

```
HTTP request → Router (auth check in deps) → Service → (ML pipeline / ORM) → DB
```

Dependencies in `backend/app/core/deps.py`:

- `get_current_user` — validates the Bearer JWT, loads the user
- `require_roles(*roles)` — RBAC guard (admin/faculty/student)
- `get_faculty_or_admin` — for endpoints accessible to faculty and admins

### Key routers

| Router | Prefix | Notes |
|---|---|---|
| auth | `/auth` | login (JSON + OAuth2 form), token introspection |
| students | `/students` | list/search/filter/sort, profile, performance, attendance, engagement |
| predictions | `/predictions` | run prediction for a student, list history |
| interventions | `/interventions` | create, list, update status (completion stamps date) |
| analytics | `/analytics` | dashboard KPIs, correlations, intervention impact |
| datasets | `/datasets` | upload CSV, validate, list |
| models | `/models` | train, list versions, detail (importance/confusion matrix), activate |
| reports | `/reports` | per-student report JSON + CSV |
| notifications | `/notifications` | list, mark read |
| admin | `/admin` | departments, sections, subjects, faculty (admin only) |
| meta | `/me`, `/departments`, etc. | current user profile, reference data |

## Frontend

```
frontend/src/
├── components/
│   ├── charts/          # Recharts wrappers (risk donut, trends, scatter, ...)
│   ├── layout/          # AppShell: sidebar, topbar, notification bell, search
│   ├── shared/          # RiskBadge, EmptyState, etc.
│   └── ui/              # Radix-based primitives (button, dialog, select, ...)
├── context/             # AuthContext (JWT + role), ThemeContext (dark mode)
├── lib/                 # api.ts fetch wrapper, utils (formatters)
├── pages/               # one file per route
└── types/               # shared TypeScript interfaces
```

### Data flow

- `lib/api.ts` wraps `fetch` with the `/api` base; on 401 it dispatches `edupredict:unauthorized` which logs the user out.
- TanStack Query caches server state per page; mutations invalidate relevant queries.
- Route guards (`Protected`, `RedirectIfAuthed` in `App.tsx`) redirect by role: `/` → student dashboard, `/dashboard` → faculty/admin.

### State

| Concern | Mechanism |
|---|---|
| Auth | localStorage JWT + `AuthContext` (profile fetched via `/me`) |
| Server data | TanStack Query |
| Theme | `ThemeContext` (class on `<html>`, persisted) |
| Toasts | sonner |

## ML Service

`MLService` (singleton in `backend/app/services/ml_service.py`):

- `train(dataset_id, db, uploader)` — loads dataset rows, trains both models, selects best, persists artifacts, deactivates older active versions, notifies the trainer
- `predict_for_student(db, student, features)` — loads the **active production model**, predicts, explains (per-factor contributions), generates recommendations, persists a `Prediction` row, and emits an early-warning notification if risk escalated vs the student's previous prediction
- `validate_dataset(df)` / `preprocess_data(df)` — input checks and z-score standardization

Model artifacts live in `models/`:

- `<algorithm>_<timestamp>_model.joblib` — trained estimator
- `<algorithm>_<timestamp>_preprocessor.joblib` — fitted `StandardScaler`
- `<algorithm>_<timestamp>_meta.json` — metrics, feature list, training rows, timestamp

## Auth & Security

- Passwords: bcrypt (`bcrypt.hashpw`/`checkpw` — passlib is not used; bcrypt 5.x removed legacy `__about__` and passlib is incompatible)
- Tokens: JWT HS256, 60-minute expiry, sub = user id
- Emails are plain `str` (not `EmailStr`) because `email-validator` rejects reserved domains like `.local` used by demo accounts
- CORS: single origin from settings `FRONTEND_URL`
