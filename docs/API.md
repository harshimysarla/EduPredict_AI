# API Reference

Base URL: `http://127.0.0.1:8000` (dev). Interactive docs at `/docs` (Swagger UI) and `/redoc`.

All endpoints except login require `Authorization: Bearer <jwt>`.

Roles: **A** = admin, **F** = faculty/advisor, **S** = student.

## Auth & Profile

| Method | Path | Roles | Description |
|---|---|---|---|
| POST | `/auth/login` | – | JSON login `{email, password}` → `{access_token, token_type}` |
| POST | `/auth/token` | – | OAuth2 form login (`username`/`password`) → token |
| GET | `/me` | A F S | Current user + role |
| GET | `/student/me` | S | Current student profile |
| GET | `/faculty/me` | F | Current faculty profile |

## Reference Data

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/departments` | A F S | Departments with sections |
| GET | `/sections?department_id=` | A F S | Sections |
| GET | `/subjects?department_id=` | A F S | Subjects |

## Students

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/students` | A F | List; query params: `search`, `department_id`, `section_id`, `risk` (`low`/`moderate`/`high`), `page`, `page_size`, `sort_by`, `sort_order` |
| POST | `/students` | A | Create student (creates user + profile) |
| GET | `/students/{id}` | A F | Profile summary + current risk |
| PUT | `/students/{id}` | A F | Update (incl. activate/deactivate) |
| GET | `/students/{id}/performance` | A F | Per-semester academic records + trends |
| GET | `/students/{id}/attendance` | A F | Monthly attendance per semester |
| GET | `/students/{id}/engagement` | A F | Monthly engagement series |

## Predictions

| Method | Path | Roles | Description |
|---|---|---|---|
| POST | `/predictions?student_id=` | A F | Run prediction `{attendance, previous_performance, internal_marks, assignment_score, engagement, study_hours}` → probability, level, factors (contributions), recommendations |
| GET | `/predictions?student_id=&limit=` | A F S | Prediction history (students see only their own) |

## Interventions

| Method | Path | Roles | Description |
|---|---|---|---|
| POST | `/interventions` | A F | Create `{student_id, type, title, description}` |
| GET | `/interventions?status=&student_id=` | A F | List |
| PUT | `/interventions/{id}` | A F | Update status/notes; `completed` sets `completed_date` |

## Analytics

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/analytics/dashboard` | A F | KPIs, risk distribution, attendance/engagement/score distributions, correlations |
| GET | `/analytics/intervention-impact?student_id=` | A F | Risk before/after + performance/attendance deltas per student |

## Datasets

| Method | Path | Roles | Description |
|---|---|---|---|
| POST | `/datasets/upload` | A F | multipart CSV + `name` → dataset row with preview |
| GET | `/datasets` | A F | List |
| GET | `/datasets/{id}/validate` | A F | Validation report (schema/range checks) |

## Models

| Method | Path | Roles | Description |
|---|---|---|---|
| POST | `/models/train` | A F | `{dataset_id}` → trains both algorithms, selects best, versioned, active |
| GET | `/models` | A F | All versions (newest first), `is_active` flag |
| GET | `/models/{id}` | A F | Detail: metrics, confusion matrix, feature importance |
| POST | `/models/{id}/activate` | A F | Promote version (deactivates others) |

## Reports

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/reports/student/{id}` | A F | Full JSON report: profile, health metrics, history, interventions |
| GET | `/reports/student/{id}/csv` | A F | Same report as CSV download |

## Notifications

| Method | Path | Roles | Description |
|---|---|---|---|
| GET | `/notifications` | A F S | Own notifications (unread first) |
| POST | `/notifications/{id}/read` | A F S | Mark as read |

## Admin

| Method | Path | Roles | Description |
|---|---|---|---|
| POST | `/admin/departments` | A | Create department (409 on duplicate code) |
| POST | `/admin/sections` | A | Create section |
| POST | `/admin/subjects` | A | Create subject |
| POST | `/admin/faculty` | A | Create faculty account |

## Common Behaviors

- **401** — missing/invalid/expired token
- **403** — authenticated but wrong role
- **422** — validation error (missing field, out-of-range value, invalid type)
- **404** — resource not found
- **409** — uniqueness conflict (e.g. duplicate department code)
- **400** — business rule violation (e.g. unknown intervention type)

## Authz Rules (enforced and tested)

- Students can never read other students' data (profiles, predictions, interventions)
- Students cannot access `/students`, `/analytics`, `/models`, `/datasets`, `/admin`
- Faculty can do everything except admin management and student creation (admin-only)
- Role checks are applied per route via `require_roles(...)` dependencies
