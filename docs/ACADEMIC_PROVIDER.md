# Academic Data Provider

EduPredict decouples the application from its academic data source through a provider abstraction (`backend/app/providers/`).

## Contract

`AcademicDataProvider` (abstract, `base.py`) — every provider exposes:

| Method | Purpose |
|---|---|
| `get_student_profile(student_id)` | load a `Student` by our internal id (abstract) |
| `get_attendance / get_academic_records / get_assessment_records / get_assignment_records / get_engagement` | per-student record rows, optional semester filter |
| `get_performance_history(student_id)` | ordered (semester, label, score) trend |
| `get_class_students(faculty_user)` | department-scoped student list (admins see all) |
| `source()` | its own `DataSource` row |

Providers read/write through the application database; they differ in **provenance** (where the rows came from), not in storage.

## Registry

`backend/app/providers/__init__.py` maps source type → class:

```python
PROVIDER_BY_TYPE = {
    "DEMO":     DemoAcademicDataProvider,
    "CSV":      CsvAcademicDataProvider,
    "SAMVIDHA": SamvidhaAcademicDataProvider,
}
```

## Selecting the active provider

```python
from app.providers import get_active_provider, activate_data_source
provider = get_active_provider(db)          # reads data_sources.status == ACTIVE
activate_data_source(db, "CSV")             # demotes current ACTIVE, promotes CSV
```

- `ensure_default_sources(db)` creates the three default rows if missing.
- `activate_data_source` raises `ProviderNotConfigured` for `NOT_CONFIGURED` sources → API returns 400.
- If no source is ACTIVE, `get_active_provider` falls back to `DEMO`.

Endpoints: `GET /data-source` (current active + `samvidha_status`), `GET /admin/data-sources`, `POST /admin/data-sources/{type}/activate`.

## Implementations

### DemoAcademicDataProvider (`DEMO`)
Default. All student data comes from the seed script (`scripts/seed_database.py`) — synthetic records consistent with the documented risk formula. Nothing dereferences external systems.

### CsvAcademicDataProvider (`CSV`)
Serves data committed by the approved CSV import flow (`POST /datasets/import`). Reads the same record tables, so switching DEMO → CSV changes **provenance only** — dashboards, summaries, and reports behave identically. See [CSV Import](CSV_IMPORT.md).

### SamvidhaAcademicDataProvider (`SAMVIDHA`)
Registration-only placeholder, inherits the default reading methods. Its `DataSource` row ships `NOT_CONFIGURED` and activation is refused. EduPredict is **not** connected to IARE Samvidha through any unofficial channel. See [Samvidha Future Integration](SAMVIDHA_FUTURE_INTEGRATION.md).

## Adding a new source

1. Subclass `AcademicDataProvider` with `type`/`display_name`.
2. Register in `PROVIDER_BY_TYPE` and `ensure_default_sources` (base.py).
3. Implement ingestion (e.g. a sync job writing record rows).
4. Admin can then switch to it from Settings → Data Sources.