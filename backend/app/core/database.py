import os
import json
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger("edupredict.database")

Base = declarative_base()


def _build_engine():
    db_url = settings.DATABASE_URL
    is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

    # If in serverless and pointing to localhost, fallback to SQLite in /tmp
    if is_serverless and ("localhost" in db_url or "127.0.0.1" in db_url):
        logger.warning("Localhost DATABASE_URL detected on serverless. Falling back to SQLite /tmp/edupredict.db")
        db_url = "sqlite:////tmp/edupredict.db"

    if db_url.startswith("sqlite"):
        return create_engine(db_url, connect_args={"check_same_thread": False})
    
    try:
        eng = create_engine(db_url, pool_pre_ping=True)
        # Test connection quickly
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return eng
    except Exception as exc:
        logger.warning("Failed to connect to %s (%s). Falling back to SQLite.", db_url, exc)
        fallback_path = "/tmp/edupredict.db" if is_serverless else "./edupredict.db"
        return create_engine(f"sqlite:///{fallback_path}", connect_args={"check_same_thread": False})


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and auto-seed base demo accounts if empty."""
    from app import models
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        from app.models import User, UserRole, Department, Section, Subject, Student, FacultyProfile, PortalDataset, Semester, SystemSetting
        from app.core.security import get_password_hash
        from app.data.students import PORTAL_DATASETS

        # Check if users already exist
        if db.query(User).first() is not None:
            return

        logger.info("Auto-seeding initial users and demo dataset...")

        # 1. Admin user
        admin = User(
            username="admin",
            hashed_password=get_password_hash("Admin@123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            email="admin@edupredict.local",
            is_active=True,
        )
        db.add(admin)

        # 2. Departments
        depts_data = [
            ("Computer Science & Engineering", "CSE"),
            ("Electronics & Communication", "ECE"),
            ("Mechanical Engineering", "MECH"),
            ("Civil Engineering", "CIVIL"),
            ("Information Technology", "IT"),
        ]
        dept_map = {}
        for name, code in depts_data:
            dept = Department(name=name, code=code, description=f"{name} department")
            db.add(dept)
            db.flush()
            dept_map[code] = dept

        # 3. Faculty Accounts
        faculty_users = {
            "CSE": ("faculty", "Prof. CSE Faculty"),
            "ECE": ("faculty.ece", "Prof. ECE Faculty"),
            "MECH": ("faculty.mech", "Prof. MECH Faculty"),
            "CIVIL": ("faculty.civil", "Prof. CIVIL Faculty"),
            "IT": ("faculty.it", "Prof. IT Faculty"),
        }
        for code, (uname, fname) in faculty_users.items():
            f_user = User(
                username=uname,
                hashed_password=get_password_hash("Faculty@123"),
                full_name=fname,
                role=UserRole.FACULTY,
                email=f"{uname}@edupredict.local",
                is_active=True,
            )
            db.add(f_user)
            db.flush()
            db.add(FacultyProfile(
                user_id=f_user.id,
                employee_id=f"EMP{code}",
                department_id=dept_map[code].id,
                designation="Associate Professor",
            ))

        # 4. Sections & Subjects
        cse_dept = dept_map["CSE"]
        sec_a = Section(name="CSE-A", department_id=cse_dept.id, academic_year="2025-2026", semester=1)
        sec_b = Section(name="CSE-B", department_id=cse_dept.id, academic_year="2025-2026", semester=1)
        sec_c = Section(name="CSE-C", department_id=cse_dept.id, academic_year="2025-2026", semester=1)
        db.add_all([sec_a, sec_b, sec_c])
        db.flush()

        # 5. Meta / Settings
        db.add(Semester(name="Semester 1", semester=1, academic_year="2025-2026", is_current=True))
        db.add(SystemSetting(key="risk_low", value="0.39"))
        db.add(SystemSetting(key="risk_high", value="0.69"))

        # 6. Portal Demo Students
        for ds in PORTAL_DATASETS:
            uname = ds.get("username") or ds.get("studentId") or ds.get("rollNumber")
            if not uname:
                continue
            name = (ds.get("profile") or {}).get("name") or ds.get("name") or uname
            passw = ds.get("password") or "demo123"
            
            s_user = User(
                username=uname.strip().lower(),
                hashed_password=get_password_hash(passw),
                full_name=name,
                role=UserRole.STUDENT,
                email=f"{uname.lower()}@student.edupredict.local",
                is_active=True,
            )
            db.add(s_user)
            db.flush()

            student = Student(
                user_id=s_user.id,
                student_id=uname,
                section_id=sec_a.id,
                admission_year=2023,
                current_semester=int(ds.get("currentSemester") or 5),
            )
            db.add(student)
            db.flush()

            db.add(PortalDataset(student_id=student.id, data=json.dumps(ds)))

        db.commit()
        logger.info("Database auto-seeding completed successfully.")
    except Exception as exc:
        db.rollback()
        logger.exception("Error during auto-seeding: %s", exc)
    finally:
        db.close()