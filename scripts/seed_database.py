import os
import random
import sys
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
    AcademicRecord, AttendanceRecord, EngagementRecord, Prediction, RiskLevel,
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
        ("Data Structures", "CSE201"),
        ("Database Systems", "CSE202"),
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


def seed(db: Session):
    rng = np.random.default_rng(SEED)
    random.seed(SEED)

    print("Seeding base data...")

    # Admin
    admin_user = db.query(User).filter(User.email == "admin@edupredict.local").first()
    if not admin_user:
        admin_user = User(
            email="admin@edupredict.local",
            hashed_password=get_password_hash("Admin@123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
        )
        db.add(admin_user)
        db.flush()
        print("  Created admin account (admin@edupredict.local / Admin@123)")

    faculty_profiles = {}
    departments = {}
    sections = []
    subjects_by_code = {}

    for idx, (name, code) in enumerate(DEPARTMENTS):
        dept = db.query(Department).filter(Department.code == code).first()
        if not dept:
            dept = Department(name=name, code=code, description=f"{name} department")
            db.add(dept)
            db.flush()
        departments[code] = dept

    # Faculty
    faculty_emails = {
        "CSE": "faculty@edupredict.local",
        "ECE": "faculty.ece@edupredict.local",
        "MECH": "faculty.mech@edupredict.local",
        "CIVIL": "faculty.civil@edupredict.local",
        "IT": "faculty.it@edupredict.local",
    }
    for code, email in faculty_emails.items():
        existing = db.query(FacultyProfile).filter(FacultyProfile.employee_id == f"EMP{code}").first()
        if existing:
            faculty_profiles[code] = existing
            continue
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = create_user(db, email, "Faculty@123", f"Prof. {departments[code].name.split(' & ')[0]}", UserRole.FACULTY)
        fp = FacultyProfile(
            user_id=user.id,
            employee_id=f"EMP{code}",
            department_id=departments[code].id,
            designation="Associate Professor",
        )
        db.add(fp)
        db.flush()
        faculty_profiles[code] = fp
        print(f"  Created faculty account ({email} / Faculty@123)")

    # Sections: A, B per department, 2 semesters
    for code, dept in departments.items():
        for sem_year in [("2025-2026", 1), ("2025-2026", 2), ("2024-2025", 1)]:
            for section_letter in ["A", "B"]:
                name = f"{code}-{section_letter}"
                sec = (
                    db.query(Section)
                    .filter(
                        Section.name == name,
                        Section.department_id == dept.id,
                        Section.academic_year == sem_year[0],
                        Section.semester == sem_year[1],
                    )
                    .first()
                )
                if not sec:
                    sec = Section(
                        name=name,
                        department_id=dept.id,
                        academic_year=sem_year[0],
                        semester=sem_year[1],
                    )
                    db.add(sec)
                    db.flush()
                sections.append(sec)

    # Subjects
    for code, subjects in SUBJECTS_BY_DEPT.items():
        for name, subj_code in subjects:
            subject = db.query(Subject).filter(Subject.code == subj_code).first()
            if not subject:
                subject = Subject(
                    name=name,
                    code=subj_code,
                    department_id=departments[code].id,
                    credits=3,
                    semester=1 if int(subj_code[-1]) % 2 == 1 else 2,
                )
                db.add(subject)
                db.flush()
            subjects_by_code[subj_code] = subject

    db.commit()
    print("  Departments, sections, subjects created")

    # Students: ~260
    print("Generating students...")
    synthetic = generate_synthetic_dataset(260, seed=SEED)

    main_sections = [s for s in sections if s.academic_year == "2025-2026" and s.semester == 1]

    # Dedicated demo student account (student@edupredict.local / Student@123)
    demo_user = db.query(User).filter(User.email == "student@edupredict.local").first()
    if not demo_user:
        demo_user = create_user(db, "student@edupredict.local", "Student@123", "Demo Student", UserRole.STUDENT)
        demo_student = Student(
            user_id=demo_user.id,
            student_id="CSE2024001",
            section_id=main_sections[0].id,
            admission_year=2024,
            current_semester=1,
        )
        db.add(demo_student)
        db.flush()
        row = synthetic.iloc[0]
        demo_sid = demo_student.id
        for j, (subj_name, subj_code) in enumerate(SUBJECTS_BY_DEPT["CSE"][:4]):
            internal = float(np.clip(row["internal_marks"] + rng.normal(0, 4), 20, 98).round(1))
            assignment = float(np.clip(row["assignment_score"] + rng.normal(0, 5), 20, 98).round(1))
            exam = float(np.clip(internal + rng.normal(6, 6), 20, 98).round(1))
            total = float(np.clip(0.4 * internal + 0.2 * assignment + 0.4 * exam, 20, 98).round(1))
            db.add(AcademicRecord(
                student_id=demo_sid, subject_id=subjects_by_code[subj_code].id,
                semester=1, internal_marks=internal, assignment_score=assignment,
                exam_score=exam, total_score=total,
                grade="A" if total >= 80 else "B",
            ))
        for k in range(8):
            held = 20 + (k * 7) % 15
            attended = max(1, int(held * 0.82))
            db.add(AttendanceRecord(
                student_id=demo_sid, subject_id=subjects_by_code[SUBJECTS_BY_DEPT["CSE"][k % 4][1]].id,                semester=1, month=k + 1, classes_held=held, classes_attended=attended,
                attendance_percentage=round(attended / held * 100, 1),
            ))
            db.add(EngagementRecord(
                student_id=demo_sid, semester=1, month=k + 1,
                participation_score=68.0, lms_logins=25 + k, forum_posts=4 + k,
                study_hours=5.0, engagement_score=68.0,
            ))
        db.add(Prediction(
            student_id=demo_sid, risk_probability=0.21, risk_level=RiskLevel.LOW,
            model_name="Synthetic Probability (Seed)", model_version="v0",
            prediction_date=datetime.utcnow() - timedelta(days=25),
        ))
        db.add(Intervention(
            student_id=demo_sid, faculty_id=faculty_profiles["CSE"].id,
            type=InterventionType.MENTOR_MEETING, title="Mentor meeting",
            description="Routine progress review with mentor.",
            status=InterventionStatus.IN_PROGRESS,
            assigned_date=datetime.utcnow() - timedelta(days=10),
            follow_up_date=datetime.utcnow() + timedelta(days=7),
            notes="Monitoring study plan adherence.",
        ))
        print("  Created demo student account (student@edupredict.local / Student@123)")

    students_created = 0
    for i in range(260):
        code = DEPARTMENTS[i % len(DEPARTMENTS)][1]
        sec_letter = "A" if (i // 5) % 2 == 0 else "B"
        section = next(
            (s for s in main_sections if s.department_id == departments[code].id and s.name == f"{code}-{sec_letter}"),
            main_sections[i % len(main_sections)],
        )
        sid = f"{code}{2026 - (i % 3)}{i:03d}"
        if db.query(Student).filter(Student.student_id == sid).first():
            continue

        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last = LAST_NAMES[(i * 7) % len(LAST_NAMES)]
        full_name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{i}@student.edupredict.local"

        row = synthetic.iloc[i]
        student = Student(
            user_id=create_user(
                db, email, "Student@123", full_name, UserRole.STUDENT
            ).id,
            student_id=sid,
            section_id=section.id,
            admission_year=2024 + (i % 2),
            current_semester=1 + (i % 2),
        )
        db.add(student)
        db.flush()

        student_id = student.id
        subj_codes = [s[1] for s in SUBJECTS_BY_DEPT[code]]
        sem = student.current_semester

        # Academic records for 2 semesters
        for sem_idx in [1, 2]:
            for j, subj_code in enumerate(subj_codes[:4]):
                base = row["internal_marks"] + rng.normal(0, 4) + (sem_idx - 1) * 4
                internal = float(np.clip(base, 20, 98).round(1))
                assignment = float(np.clip(row["assignment_score"] + rng.normal(0, 5) + (sem_idx - 1) * 3, 20, 98).round(1))
                exam = float(np.clip(internal + rng.normal(6, 6), 20, 98).round(1))
                total = float(np.clip(0.4 * internal + 0.2 * assignment + 0.4 * exam, 20, 98).round(1))
                grade = "A" if total >= 80 else "B" if total >= 65 else "C" if total >= 50 else "D" if total >= 40 else "F"
                db.add(
                    AcademicRecord(
                        student_id=student_id,
                        subject_id=subjects_by_code[subj_code].id,
                        semester=sem_idx,
                        internal_marks=internal,
                        assignment_score=assignment,
                        exam_score=exam,
                        total_score=total,
                        grade=grade,
                    )
                )

        # Attendance: varies by prediction risk
        base_att = row["attendance"]
        for sem_idx in [1, 2]:
            for k in range(8):  # 8 months
                att = float(np.clip(base_att + rng.normal(0, 6) + (sem_idx - 1) * 2, 15, 100).round(1))
                held = 20 + (k * 7) % 15
                attended = int(round(held * att / 100))
                db.add(
                    AttendanceRecord(
                        student_id=student_id,
                        subject_id=subjects_by_code[subj_codes[k % 4]].id,
                        semester=sem_idx,
                        month=k + 1,
                        classes_held=held,
                        classes_attended=attended,
                        attendance_percentage=round(attended / held * 100, 1) if held else 0,
                    )
                )

        # Engagement
        for sem_idx in [1, 2]:
            for k in range(8):
                eng = float(np.clip(row["engagement"] + rng.normal(0, 7) + (sem_idx - 1) * 3, 5, 100).round(1))
                study = float(np.clip(row["study_hours"] + rng.normal(0, 0.5), 0.5, 14).round(1))
                db.add(
                    EngagementRecord(
                        student_id=student_id,
                        semester=sem_idx,
                        month=k + 1,
                        participation_score=eng,
                        lms_logins=int(np.clip(eng * 0.3 + rng.normal(0, 3), 1, 90)),
                        forum_posts=int(np.clip(eng * 0.05 + rng.normal(0, 3), 0, 30)),
                        study_hours=study,
                        engagement_score=eng,
                    )
                )

        # Initial prediction using the documented synthetic risk function
        prob = compute_risk_probability(
            {
                "attendance": float(base_att),
                "previous_performance": float(row["previous_performance"]),
                "internal_marks": float(row["internal_marks"]),
                "assignment_score": float(row["assignment_score"]),
                "engagement": float(row["engagement"]),
                "study_hours": float(row["study_hours"]),
            },
            rng,
        )
        prob = float(np.clip(prob, 0.02, 0.97))
        level = RiskLevel.HIGH if prob > 0.69 else RiskLevel.MODERATE if prob > 0.39 else RiskLevel.LOW
        db.add(
            Prediction(
                student_id=student_id,
                risk_probability=round(prob, 4),
                risk_level=level,
                model_name="Synthetic Probability (Seed)",
                model_version="v0",
                prediction_date=datetime.utcnow() - timedelta(days=30 + (i % 20)),
            )
        )

        # Second prediction 2 weeks ago for most students (so trends exist)
        if i % 5 != 0:
            prob2 = float(np.clip(prob + rng.normal(0, 0.1), 0.02, 0.97))
            level2 = RiskLevel.HIGH if prob2 > 0.69 else RiskLevel.MODERATE if prob2 > 0.39 else RiskLevel.LOW
            db.add(
                Prediction(
                    student_id=student_id,
                    risk_probability=round(prob2, 4),
                    risk_level=level2,
                    model_name="Synthetic Probability (Seed)",
                    model_version="v0",
                    prediction_date=datetime.utcnow() - timedelta(days=12 + (i % 10)),
                )
            )

        if i % 3 == 0:
            # Interventions for at-risk students
            can_intervene = prob2 if i % 5 != 0 else prob
            if can_intervene > 0.35:
                i_type = (
                    InterventionType.ACADEMIC_COUNSELLING
                    if can_intervene > 0.6
                    else InterventionType.MENTOR_MEETING
                )
                fp = faculty_profiles[code]
                iv = Intervention(
                    student_id=student_id,
                    faculty_id=fp.id,
                    type=i_type,
                    title=(
                        "Academic counselling session"
                        if i_type == InterventionType.ACADEMIC_COUNSELLING
                        else "Mentor meeting for progress review"
                    ),
                    description=f"Student flagged with risk probability {can_intervene:.0%}. Scheduled follow-up to monitor progress.",
                    status=(
                        InterventionStatus.COMPLETED
                        if i % 6 == 0
                        else InterventionStatus.IN_PROGRESS
                    ),
                    assigned_date=datetime.utcnow() - timedelta(days=14 + (i % 10)),
                    follow_up_date=datetime.utcnow() + timedelta(days=7 + (i % 15)),
                    completed_date=(
                        datetime.utcnow() - timedelta(days=5)
                        if i % 6 == 0
                        else None
                    ),
                    notes="Monitoring weekly performance and attendance.",
                )
                db.add(iv)

        students_created += 1
        if students_created % 50 == 0:
            db.commit()
            print(f"  {students_created} students seeded...")

    db.commit()
    print(f"Total students seeded: {students_created}")

    # Yearly notifications for all users
    all_users = db.query(User).all()
    for u in all_users:
        notify(
            db, u.id,
            "Welcome to EduPredict AI",
            "Your account has been created. Explore your dashboard to get started.",
            "welcome",
        )
    db.commit()
    print("Seed complete!")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()