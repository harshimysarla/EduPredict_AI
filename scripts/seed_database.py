"""Seed the EduPredict AI database with demo data.

What is created:
  * 4 portal student accounts (login by roll number as username, password
    demo123) with full Samvidha-style academic portal data seeded from
    backend/app/data/students/*.json: 24951A05B1 (DEMO STUDENT TWO),
    24951A05B2 (DEMO STUDENT THREE), 24951A05B3 (MYSARLA HARSHITH),
    24951A05B4 (DEMO STUDENT FOUR).
  * 260 additional students (usernames student001..student260) covering all
    departments with realistic variation (high/moderate/low risk).
  * Admin + faculty accounts per department.
  * Data source registry (DEMO active, CSV available, SAMVIDHA not configured),
    semester reference data, and default risk threshold settings.

All academic data is SYNTHETIC DEMO DATA generated with the documented
calibration (backend/app/ml/dataset_generator.py, seed=42). It must never be
presented as real IARE student data. Login is by username + password.
"""
import os
import random
import sys
import json
from datetime import datetime, timedelta

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _repo_root)
sys.path.insert(0, os.path.join(_repo_root, "backend"))

import numpy as np
from sqlalchemy.orm import Session

from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models import (
    User, UserRole, Department, Section, Subject, Student, FacultyProfile,
    AcademicRecord, AttendanceRecord, EngagementRecord, AssessmentRecord,
    AssignmentRecord, Prediction, RiskLevel, Semester, SystemSetting,
    Intervention, InterventionType, InterventionStatus, Notification,
)
from app.services.base import create_user, notify
from app.ml.dataset_generator import generate_synthetic_dataset, compute_risk_probability

SEED = 42

DEPARTMENTS = [
    ("Computer Science & Engineering", "CSE"),
    ("Electronics & Communication", "ECE"),
    ("Mechanical Engineering", "MECH"),
    ("Civil Engineering", "CIVIL"),
    ("Information Technology", "IT"),
]

SUBJECTS_BY_DEPT = {
    "CSE": [
        ("Database Management Systems", "CSE201"),
        ("Design & Analysis of Algorithms", "CSE202"),
        ("Operating Systems", "CSE203"),
        ("Machine Learning", "CSE204"),
        ("Computer Networks", "CSE205"),
    ],
    "ECE": [
        ("Digital Electronics", "ECE201"),
        ("Signals & Systems", "ECE202"),
        ("Microprocessors", "ECE203"),
        ("Communication Systems", "ECE204"),
        ("VLSI Design", "ECE205"),
    ],
    "MECH": [
        ("Thermodynamics", "MECH201"),
        ("Fluid Mechanics", "MECH202"),
        ("Machine Design", "MECH203"),
        ("Manufacturing Processes", "MECH204"),
        ("Dynamics of Machines", "MECH205"),
    ],
    "CIVIL": [
        ("Structural Analysis", "CIV201"),
        ("Geotechnical Engineering", "CIV202"),
        ("Transportation Engineering", "CIV203"),
        ("Environmental Engineering", "CIV204"),
        ("Surveying", "CIV205"),
    ],
    "IT": [
        ("Web Technologies", "IT201"),
        ("Software Engineering", "IT202"),
        ("Cloud Computing", "IT203"),
        ("Data Analytics", "IT204"),
        ("Cryptography", "IT205"),
    ],
}

FIRST_NAMES = [
    "Aarav", "Aditi", "Arjun", "Ananya", "Rohan", "Riya", "Vikram", "Sneha",
    "Karan", "Priya", "Rahul", "Neha", "Amit", "Pooja", "Sanjay", "Kavya",
    "Suresh", "Divya", "Nikhil", "Shreya", "Varun", "Meera", "Deepak", "Ishita",
    "Ravi", "Anjali", "Mohan", "Lakshmi", "Gaurav", "Tanvi", "Abhishek", "Nisha",
    "Siddharth", "Aisha", "Kunal", "Ritika", "Harsh", "Shruti", "Manish", "Payal",
    "Aditya", "Sakshi", "Rajat", "Pranavi", "Yash", "Kirti", "Om", "Jyoti",
    "Dev", "Ankita", "Tejas", "Bhavna", "Sahil", "Nivedita", "Mohit", "Swati",
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Singh", "Kumar", "Reddy", "Gupta", "Mehta",
    "Nair", "Iyer", "Das", "Bose", "Chowdhury", "Malhotra", "Khanna", "Kapoor",
    "Arora", "Bhatia", "Desai", "Joshi", "Kulkarni", "Menon", "Pillai", "Rao",
    "Saxena", "Trivedi", "Yadav", "Mishra", "Pandey", "Tiwari", "Dubey", "Chopra",
]

STUDENT_PASSWORD = "Student@123"


def _seed_reference(db: Session, departments: dict, sections: list, subjects_by_code: dict):
    for name, code in DEPARTMENTS:
        dept = db.query(Department).filter(Department.code == code).first()
        if not dept:
            dept = Department(name=name, code=code, description=f"{name} department")
            db.add(dept)
            db.flush()
        departments[code] = dept

    faculty_by_dept = {
        "CSE": "faculty",
        "ECE": "faculty.ece",
        "MECH": "faculty.mech",
        "CIVIL": "faculty.civil",
        "IT": "faculty.it",
    }
    for code, username in faculty_by_dept.items():
        existing = db.query(FacultyProfile).filter(FacultyProfile.employee_id == f"EMP{code}").first()
        if existing:
            continue
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = create_user(
                db, username, "Faculty@123",
                f"Prof. {departments[code].name.split(' & ')[0]}", UserRole.FACULTY,
                email=f"{username}@edupredict.local",
            )
        db.add(FacultyProfile(
            user_id=user.id,
            employee_id=f"EMP{code}",
            department_id=departments[code].id,
            designation="Associate Professor",
        ))
        db.flush()

    for code, dept in departments.items():
        for sem_year, sem in [("2025-2026", 1), ("2025-2026", 2), ("2024-2025", 1)]:
            for letter in ["A", "B"]:
                name = f"{code}-{letter}"
                sec = (
                    db.query(Section)
                    .filter(Section.name == name, Section.department_id == dept.id,
                            Section.academic_year == sem_year, Section.semester == sem)
                    .first()
                )
                if not sec:
                    sec = Section(name=name, department_id=dept.id,
                                  academic_year=sem_year, semester=sem)
                    db.add(sec)
                    db.flush()
                sections.append(sec)

    for code, subj_list in SUBJECTS_BY_DEPT.items():
        for name, subj_code in subj_list:
            subject = db.query(Subject).filter(Subject.code == subj_code).first()
            if not subject:
                subject = Subject(
                    name=name, code=subj_code, department_id=departments[code].id,
                    credits=3, semester=1 if int(subj_code[-1]) % 2 == 1 else 2,
                )
                db.add(subject)
                db.flush()
            subjects_by_code[subj_code] = subject

    db.commit()
    print("  Departments, sections, subjects OK")


def _seed_meta(db: Session):
    from app.providers import ensure_default_sources
    ensure_default_sources(db)

    semesters = [(1, "2025-2026", True), (2, "2025-2026", False), (3, "2024-2025", False)]
    for sem, year, current in semesters:
        if not db.query(Semester).filter(Semester.semester == sem).first():
            db.add(Semester(name=f"Semester {sem}", semester=sem,
                            academic_year=year, is_current=current))
    if not db.query(SystemSetting).filter(SystemSetting.key == "risk_low").first():
        db.add(SystemSetting(key="risk_low", value="0.39"))
        db.add(SystemSetting(key="risk_high", value="0.69"))
    db.commit()


def seed(db: Session):
    rng = np.random.default_rng(SEED)
    random.seed(SEED)

    print("Seeding base data...")
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = create_user(db, "admin", "Admin@123", "System Administrator",
                                 UserRole.ADMIN, email="admin@edupredict.local")
        db.flush()
        print("  Created admin account (admin / Admin@123)")

    departments, sections, subjects_by_code = {}, [], {}
    _seed_reference(db, departments, sections, subjects_by_code)
    _seed_meta(db)

    main_sections = [s for s in sections if s.academic_year == "2025-2026" and s.semester == 1]

    # ---------------------------------------------------------------------------
    print("Generating students...")
    synthetic = generate_synthetic_dataset(260, seed=SEED)

    def student_records(student: Student, row, semester_offsets=(1, 2), n_subjects=4, rng=rng):
        """Academic + attendance + engagement + assessment + assignment records."""
        subj_codes = [s[1] for s in SUBJECTS_BY_DEPT["CSE"][:n_subjects]]
        for sem_idx in semester_offsets:
            for j, subj_code in enumerate(subj_codes):
                base = float(row["internal_marks"]) + rng.normal(0, 4) + (sem_idx - 1) * 4
                internal = float(np.clip(base, 20, 98).round(1))
                assignment = float(np.clip(
                    row["assignment_score"] + rng.normal(0, 5) + (sem_idx - 1) * 3, 20, 98).round(1))
                exam = float(np.clip(internal + rng.normal(6, 6), 20, 98).round(1))
                total = float(np.clip(0.4 * internal + 0.2 * assignment + 0.4 * exam, 20, 98).round(1))
                grade = ("A" if total >= 80 else "B" if total >= 65 else "C"
                         if total >= 50 else "D" if total >= 40 else "F")
                db.add(AcademicRecord(
                    student_id=student.id, subject_id=subjects_by_code[subj_code].id,
                    semester=sem_idx, internal_marks=internal, assignment_score=assignment,
                    exam_score=exam, total_score=total, grade=grade,
                ))
                i1 = float(np.clip(internal - rng.normal(5, 3), 10, 98).round(1))
                i2 = float(np.clip(internal + rng.normal(3, 3), 10, 98).round(1))
                db.add(AssessmentRecord(
                    student_id=student.id, subject_id=subjects_by_code[subj_code].id,
                    semester=sem_idx, assessment_number=1, marks=i1,
                ))
                db.add(AssessmentRecord(
                    student_id=student.id, subject_id=subjects_by_code[subj_code].id,
                    semester=sem_idx, assessment_number=2, marks=i2,
                ))
                db.add(AssignmentRecord(
                    student_id=student.id, subject_id=subjects_by_code[subj_code].id,
                    semester=sem_idx, score=assignment,
                    completion_percentage=float(np.clip(assignment + rng.normal(3, 4), 5, 100).round(1)),
                ))
            base_att = float(np.clip(row["attendance"] + (sem_idx - 1) * 4, 15, 100))
            for k in range(8):
                att = float(np.clip(base_att + rng.normal(0, 5), 15, 100).round(1))
                held = 20 + (k * 7) % 15
                db.add(AttendanceRecord(
                    student_id=student.id, subject_id=subjects_by_code[subj_codes[k % n_subjects]].id,
                    semester=sem_idx, month=k + 1, classes_held=held,
                    classes_attended=int(round(held * att / 100)),
                    attendance_percentage=att,
                ))
                eng = float(np.clip(row["engagement"] + rng.normal(0, 6) + (sem_idx - 1) * 3, 5, 100).round(1))
                study = float(np.clip(row["study_hours"] + rng.normal(0, 0.5), 0.5, 14).round(1))
                db.add(EngagementRecord(
                    student_id=student.id, semester=sem_idx, month=k + 1,
                    participation_score=eng,
                    lms_logins=int(np.clip(eng * 0.3 + rng.normal(0, 3), 1, 90)),
                    forum_posts=int(np.clip(eng * 0.05 + rng.normal(0, 3), 0, 30)),
                    study_hours=study, engagement_score=eng,
                ))
        db.flush()

    def add_prediction(student: Student, prob: float, days_ago: int, model="Synthetic Probability (Seed)", version="v0"):
        prob = float(np.clip(prob, 0.02, 0.97))
        level = RiskLevel.HIGH if prob > 0.69 else RiskLevel.MODERATE if prob > 0.39 else RiskLevel.LOW
        db.add(Prediction(
            student_id=student.id, risk_probability=round(prob, 4), risk_level=level,
            model_name=model, model_version=version,
            prediction_date=datetime.utcnow() - timedelta(days=days_ago),
        ))
        db.flush()
        return prob

    # --- Portal students (Samvidha-style academic portal demo accounts) ---------
    # 4 local student accounts whose portal data (grades, attendance, SGPA, CGPA,
    # courses due) is seeded from backend/app/data/students/*.json. Login is by
    # roll number as username (password demo123). These replace the old demo trio
    # (student01/02/03) and own student ids 24951A05B1..B4.
    from app.models import PortalDataset
    from app.data.students import PORTAL_DATASETS
    for ds in PORTAL_DATASETS:
        sid = ds.get("rollNumber") or ds.get("studentId")
        if not sid:
            continue
        if db.query(Student).filter(Student.student_id == sid).first():
            continue
        profile = ds.get("profile") or {}
        name = profile.get("name") or ds.get("name") or sid
        username = str(sid).lower()
        if db.query(User).filter(User.username == username).first():
            continue
        cse_dept = departments.get("CSE")
        sec_name = f"CSE-{profile.get('section') or 'A'}"
        section = next(
            (s for s in main_sections
             if s.department_id == cse_dept.id and s.name == sec_name),
            main_sections[0],
        )
        year = int(profile.get("year") or 1)
        cur_sem = int(profile.get("currentSemester") or ds.get("currentSemester") or 1)
        user = create_user(db, username, "demo123", name, UserRole.STUDENT)
        student = Student(
            user_id=user.id, student_id=sid, section_id=section.id,
            admission_year=2026 - year, current_semester=cur_sem,
        )
        db.add(student)
        db.flush()
        db.add(PortalDataset(student_id=student.id, data=json.dumps(ds)))
        print(f"  Created portal demo student ({username} / demo123 -> {sid})")

    # --- Bulk students ------------------------------------------------------------
    students_created = 0
    for i in range(260):
        code = DEPARTMENTS[i % len(DEPARTMENTS)][1]
        sec_letter = "A" if (i // 5) % 2 == 0 else "B"
        section = next(
            (s for s in main_sections if s.department_id == departments[code].id
             and s.name == f"{code}-{sec_letter}"),
            main_sections[i % len(main_sections)],
        )
        sid = f"{code}{2026 - (i % 3)}{i:03d}"
        if db.query(Student).filter(Student.student_id == sid).first():
            continue

        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last = LAST_NAMES[(i * 7) % len(LAST_NAMES)]
        full_name = f"{first} {last}"
        username = f"student{i + 1:03d}"
        if db.query(User).filter(User.username == username).first():
            continue
        email = f"{first.lower()}.{last.lower()}{i}@student.edupredict.local"

        row = synthetic.iloc[i]
        student = Student(
            user_id=create_user(db, username, STUDENT_PASSWORD, full_name, UserRole.STUDENT,
                                email=email).id,
            student_id=sid, section_id=section.id,
            admission_year=2024 + (i % 2), current_semester=1 + (i % 2),
        )
        db.add(student)
        db.flush()

        student_records(student, row, semester_offsets=(1, 2))

        prob = compute_risk_probability(
            {
                "attendance": float(row["attendance"]),
                "previous_performance": float(row["previous_performance"]),
                "internal_marks": float(row["internal_marks"]),
                "assignment_score": float(row["assignment_score"]),
                "engagement": float(row["engagement"]),
                "study_hours": float(row["study_hours"]),
            },
            rng,
        )
        add_prediction(student, prob, 30 + (i % 20))
        if i % 5 != 0:
            add_prediction(student, prob + rng.normal(0, 0.1), 12 + (i % 10))

        if i % 3 == 0:
            can_intervene = prob + (rng.normal(0, 0.1) if i % 5 != 0 else 0)
            if can_intervene > 0.35:
                i_type = (InterventionType.ACADEMIC_COUNSELLING
                          if can_intervene > 0.6 else InterventionType.MENTOR_MEETING)
                fp = db.query(FacultyProfile).filter(FacultyProfile.employee_id == f"EMP{code}").first()
                db.add(Intervention(
                    student_id=student.id, faculty_id=fp.id, type=i_type,
                    title="Academic counselling session" if i_type == InterventionType.ACADEMIC_COUNSELLING
                    else "Mentor meeting for progress review",
                    description=f"Student flagged with risk probability {can_intervene:.0%}. "
                                "Scheduled follow-up to monitor progress.",
                    status=(InterventionStatus.COMPLETED if i % 6 == 0 else InterventionStatus.IN_PROGRESS),
                    assigned_date=datetime.utcnow() - timedelta(days=14 + (i % 10)),
                    follow_up_date=datetime.utcnow() + timedelta(days=7 + (i % 15)),
                    completed_date=(datetime.utcnow() - timedelta(days=5)
                                    if i % 6 == 0 else None),
                    notes="Monitoring weekly performance and attendance.",
                ))

        students_created += 1
        if students_created % 50 == 0:
            db.commit()
            print(f"  {students_created} students seeded...")

    db.commit()
    print(f"Total students seeded: {students_created}")

    all_users = db.query(User).all()
    for u in all_users:
        if not db.query(Notification).filter(Notification.user_id == u.id,
                                             Notification.type == "welcome").first():
            notify(db, u.id, "Welcome to EduPredict AI",
                   "Your account has been created. Explore your dashboard to get started.",
                   "welcome")
    db.commit()
    print("Seed complete!")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()