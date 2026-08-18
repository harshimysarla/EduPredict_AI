# IARE Samvidha — Future Integration

## Current status

EduPredict is **NOT connected** to IARE's Samvidha platform.

- The `SAMVIDHA` data source ships with status `NOT_CONFIGURED`.
- `POST /admin/data-sources/SAMVIDHA/activate` returns 400 (`ProviderNotConfigured`) — it cannot be turned on from the UI.
- No endpoints, credentials, or scraping of Samvidha exist anywhere in the codebase, and none will be added without an official integration path.

This is a deliberate integrity measure: student records must come from an approved channel, never from reverse engineering or unofficial access.

## What would be required

An official integration would need, at minimum:

1. **Official API documentation** from IARE describing the Samvidha student-data endpoints (auth scheme, rate limits, data contracts).
2. **Provisioned credentials** (e.g. client id/secret, service account) approved for our use.
3. A signed data-handling agreement covering what data is stored and how long.

## Implementation sketch

Everything is already prepared for this:

1. Implement the existing `SamvidhaAcademicDataProvider` (currently registration-only in `backend/app/providers/samvidha_provider.py`) to fetch student, attendance, academic, assessment, assignment, and engagement data.
2. Write rows into the same record tables the other providers use (`academic_records`, `attendances`, `engagements`, `assessments`, `assignments`).
3. Add configuration (API base URL, credentials) to `backend/app/core/config.py` and `.env` — never hardcode secrets.
4. On first successful sync, flip `DataSource` status `NOT_CONFIGURED` → `AVAILABLE`; activate via the existing endpoint. The UI badge (top bar + Settings) reflects it automatically.
5. Add a scheduled sync (e.g. APScheduler/celery-beat) plus a manual "Sync now" admin action.

Because all consumers talk through `AcademicDataProvider` and read database rows, no dashboard/analytics/report changes are needed — the source switch is the only change.

## Safety rails

- Keep the `NOT_CONFIGURED` default so an unconfigured environment can never appear connected.
- Store credentials only in environment variables; treat the Samvidha token/refresh cycle like JWT secrets.
- Log sync provenance per row (`data_source` column on record tables) so any record's origin is auditable.