# EduPredict AI

AI-powered student performance prediction and early-warning system for higher education.

EduPredict AI ingests student academic, attendance and engagement data, trains interpretable ML models (Logistic Regression + Random Forest), and surfaces explainable risk predictions with recommended interventions to faculty and advisors. Students see their own risk profile, trends, and impact of interventions.

## Features

- **Role-based access** — Admin, Faculty/Advisor, Student with strict authorization
- **Explainable predictions** — per-factor contributions for every risk score
- **Early-warning engine** — risk escalation between predictions triggers notifications
- **Intervention management** — assign, update status, measure before/after impact
- **Model Lab** — dataset upload, validation, training, model versioning, activate production model
- **Analytics dashboard** — KPIs, risk distribution, attendance/engagement correlations, score distributions
- **Reports** — per-student JSON/CSV export
- **Rich frontend** — React 19 + Tailwind v4 + Recharts, dark mode, global search, notification bell

## Tech Stack

| Layer    | Technology |
|----------|-----------|
| Backend  | FastAPI, SQLAlchemy 2.0, Pydantic v2, scikit-learn, joblib |
| Database | PostgreSQL 16 (psycopg3) |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, TanStack Query, Recharts, Framer Motion, Radix UI |
| Auth     | JWT (python-jose), bcrypt |

## Quick Start

### Prerequisites

- Python 3.12+ (3.13 supported)
- Node.js 20+ and npm
- PostgreSQL 16 running locally

### 1. Backend

```bash
# create database (once)
psql -U postgres -c "CREATE DATABASE edupredict;"

cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate      # Linux/macOS

pip install -r requirements.txt
cp ../.env.example ../.env       # adjust DATABASE_URL / SECRET_KEY

# create tables and seed demo data (260 students, 5 departments, faculty, etc.)
cd ..
python scripts/seed_database.py

# start API
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs: http://127.0.0.1:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173 (Vite proxies `/api` to `http://127.0.0.1:8000`).

## Demo Accounts

| Role    | Email                        | Password     |
|---------|------------------------------|--------------|
| Admin   | admin@edupredict.local       | Admin@123    |
| Faculty | faculty@edupredict.local     | Faculty@123 |
| Student | student@edupredict.local     | Student@123 |

Additional faculty per department: `faculty.ece|mech|civil|it@edupredict.local` / `Faculty@123`.

## Demo Walkthrough

1. Log in as **admin** → Settings: manage departments, sections, subjects, faculty.
2. Log in as **faculty** → Dashboard shows KPIs; **Students** list supports search/filter/sort; open a profile to view charts and run a new prediction (feature sliders + explanation + recommendations).
3. **Model Lab** → upload `data/student_performance.csv` (600 rows), validate, train. New models are versioned; promote one to production.
4. **Predictions** → run batch-style predictions, compare trend, flag escalations.
5. **Interventions** → create mentor meetings / counselling; track status; view before/after impact on Analytics.
6. Log in as **student** → personal dashboard with own risk, trend, and recommendations.

## Tests

```bash
python -m pytest tests/test_api.py -q            # 24 API/RBAC/ML end-to-end tests
python -m pytest tests/test_ml_pipeline.py -q    # 16 ML pipeline unit tests
python tests/test_api_surface.py                 # live smoke test (requires running backend)
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [ML Pipeline & Synthetic Data](docs/ML_PIPELINE.md)
- [Database Schema](docs/DATABASE.md)
- [API Reference](docs/API.md)
- [Demo Guide](docs/DEMO_GUIDE.md)

## Project Layout

```
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers (auth, students, predictions, ...)
│   │   ├── core/           # config, database, security, deps
│   │   ├── ml/             # dataset generator, ML pipeline
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # business logic, ML service, base helpers
│   └── requirements.txt
├── frontend/               # React + Vite + Tailwind v4
├── scripts/seed_database.py
├── data/student_performance.csv   # synthetic dataset (600 rows)
├── models/                 # trained model artifacts (joblib)
├── uploads/                # uploaded datasets
└── docs/
```

## Security Notes

- Demo credentials only — change the JWT `SECRET_KEY` and all passwords before any real deployment.
- `SECRET_KEY` must be ≥ 32 characters.
- CORS is restricted to `FRONTEND_URL` (default `http://localhost:5173`).
