# CSV Academic Import

Faculty/admins can import approved academic data as CSV. The flow lives in `backend/app/providers/csv_provider.py`, exposed via `POST /datasets/import/validate` and `POST /datasets/import` (UI: **Settings → Data Sources → Approved Academic Import**, or the Dataset / Academic Import page).

## File format

One row per student–subject–semester combination. Required columns:

`student_id, student_name, department, section, semester, subject, attendance, internal_1, internal_2, assignment_score, previous_performance, engagement, target`

- `student_id` — external roll number; also recognised under aliases `roll_number`, `roll_no`, `id`.
- `subject` — matched by **code or name** against seeded subjects (e.g. `CSE201` or the full name).
- `semester` — numeric; the row lands in that semester unit.
- `target` — 1 (at risk) / 0 (not at risk) — used for reference, not to mutate predictions.
- Remaining fields — numeric percentages/scores, parsed with bounds checks.

## Validation (`/datasets/import/validate`)

Dry-run report:

| Field | Meaning |
|---|---|
| `rows` / `valid_rows` / `rejected` | counts of the whole file |
| `will_create_students` | students in the file that don't exist yet (created again on export) |
| `preview` | first valid rows |
| `errors` / `error_lines` | per-row problems (missing required columns, unknown subject, unknown student without `student_name`, non-numeric values) |

No DB writes happen on validate.

## Commit (`/datasets/import`)

1. **Create users/students** for unseen `student_id`s — username `u{student_id.lower()}`, **placeholder password `"!"` (no working password)** — an admin must reset it before the student can log in.
2. **Upsert** records per student/subject/semester (re-importing the same file is idempotent):
   - `AcademicRecord` (internal marks 1/2, assignment score, total, grade)
   - `AssessmentRecord` (internal_1 → assessment 1, internal_2 → assessment 2)
   - `AssignmentRecord`, `AttendanceRecord`, `EngagementRecord`
3. Switches the **CSV source to ACTIVE** (DEMO → AVAILABLE) and records a `Dataset` history row used by `/datasets/imports/history`.

Response: `{"imported": true, "imported_rows", "created_students": [ids...], "warnings", "rejected", "errors_total", "source_status", "record_count"}`.

## Notes

- Imported students get no password by design — provisioning credentials is an admin action.
- Importing doesn't compute predictions; run a prediction per student (or wait for the next batch) as usual. Risk levels shown elsewhere come from the students' latest `predictions` rows.
- Required-field rule: `student_id`, `subject`, `semester` must resolve; other columns missing in the file are tolerated with warnings.