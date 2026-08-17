# Database Schema

PostgreSQL 16, database `edupredict`. Managed via SQLAlchemy 2.0 ORM (`Base.metadata.create_all` for new installs; Alembic is configured in `backend/migrations/` for future schema evolution).

## Entity Overview

```
User ─┬─ FacultyProfile ──┐
      └─ Student ──┬── Section ─ Department
                   ├── Subject ─ Department
                   ├── AcademicRecord   (per student/subject/semester)
                   ├── AttendanceRecord (per student/subject/month)
                   ├── EngagementRecord (per student/month)
                   ├── Prediction       (risk history)
                   └── Intervention     (faculty-assigned actions)

Dataset ── ModelVersion (trained artifacts, is_active flag)
Notification ── User (feed for dashboard bell)
```

## Tables

### users
| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| email | varchar UNIQUE | demo uses `.local` domains |
| password_hash | varchar | bcrypt |
| full_name | varchar | |
| role | varchar | `admin` \| `faculty` \| `student` |
| is_active | bool | soft disable |
| created_at | timestamp | |

### departments, sections, subjects
| Table | Key columns |
|---|---|
| departments | code UNIQUE (CSE, ECE, MECH, CIVIL, IT), name, description |
| sections | name (`CSE-A` …), department_id FK |
| subjects | code UNIQUE (CSE201 …), name, credits, department_id FK |

### students
| Column | Notes |
|---|---|
| id | PK |
| user_id | FK → users (1:1 with UserRole.STUDENT) |
| student_id | UNIQUE, e.g. `CSE2024001` |
| section_id | FK → sections |
| admission_year, current_semester | |

### faculty_profiles
| Column | Notes |
|---|---|
| id | PK |
| user_id | FK → users (1:1 with UserRole.FACULTY) |
| department_id | FK → departments |
| designation | e.g. Professor |

### academic_records
| Column | Notes |
|---|---|
| student_id, subject_id, semester | FKs |
| internal_marks, assignment_score, exam_score, total_score | 0–100 |
| grade | A/B/C/D/F derived from total_score |

### attendance_records
| Column | Notes |
|---|---|
| student_id, subject_id, semester, month | FKs |
| classes_held, classes_attended | |
| attendance_percentage | derived |

### engagement_records
| Column | Notes |
|---|---|
| student_id, semester, month | FKs |
| participation_score, lms_logins, forum_posts, study_hours, engagement_score | |

### predictions
| Column | Notes |
|---|---|
| student_id | FK |
| risk_probability | float 0–1 |
| risk_level | `low` \| `moderate` \| `high` |
| model_name, model_version | provenance |
| prediction_date | |

### interventions
| Column | Notes |
|---|---|
| student_id, faculty_id | FKs |
| type | `mentor_meeting` \| `academic_counselling` \| `parent_meeting` \| `study_group` \| `tutoring` |
| title, description, notes | |
| status | `planned` \| `in_progress` \| `completed` \| `cancelled` |
| assigned_date, follow_up_date, completed_date | |

### datasets
| Column | Notes |
|---|---|
| name, filename, file_path | uploaded CSV |
| row_count, status | `uploaded` \| `validated` \| `trained` |
| uploader_id | FK → users |

### model_versions
| Column | Notes |
|---|---|
| model_id | artifact identifier |
| algorithm | `Logistic Regression` \| `Random Forest` |
| dataset_id | FK → datasets |
| accuracy, precision, recall, f1_score, roc_auc | test-set metrics |
| feature_list | JSON |
| training_rows | |
| is_active | exactly one at a time (enforced by service logic) |
| model_path, preprocessor_path, metrics | artifact locations / JSON |
| training_date | |

### notifications
| Column | Notes |
|---|---|
| user_id | FK |
| title, message, type | `welcome`, `prediction_alert`, `model_trained`, … |
| is_read | |
| created_at | |

## Relationships Summary

- Student has many: academic_records, attendance_records, engagement_records, predictions, interventions
- Faculty has many: interventions (as assignee)
- Department has many: sections, subjects, faculty_profiles
- User has one: student or faculty profile
- Dataset has many: model_versions

## Seed Data (scripts/seed_database.py)

- 5 departments, 10 sections (A/B per dept), 25 subjects (5 per dept)
- 6 faculty accounts (1 per department + demo) + admin
- 260 students (with per-student user accounts), 2 semesters × 4 subjects of records
- 2 predictions per student (30 days and ~12 days ago), interventions for at-risk students
- Welcome notifications for all users
- Demo student `CSE2024001` (student@edupredict.local) with clean LOW-risk profile

All data is regenerated from the documented synthetic generator (`seed=42`) so risk levels and trends are consistent between the database and `data/student_performance.csv`.
