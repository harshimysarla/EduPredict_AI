import os
import json
import logging
import tempfile

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger("edupredict.database")
Base = declarative_base()

# ── engine is created lazily (not at import time) ─────────────────
_engine = None
_SessionLocal = None


def _build_engine():
    from app.core.config import settings

    db_url = settings.DATABASE_URL
    is_linux = (os.name != "nt")
    tmp_sqlite = f"sqlite:///{os.path.join(tempfile.gettempdir(), 'edupredict.db')}"

    # Always fall back to SQLite on serverless if URL points to localhost
    if is_linux and ("localhost" in db_url or "127.0.0.1" in db_url or db_url.startswith("sqlite:///./")):
        db_url = tmp_sqlite

    if db_url.startswith("sqlite"):
        return create_engine(db_url, connect_args={"check_same_thread": False})

    try:
        eng = create_engine(db_url, pool_pre_ping=True, pool_timeout=5, connect_args={"connect_timeout": 5})
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return eng
    except Exception as exc:
        logger.warning("DB connect failed (%s) → falling back to SQLite", exc)
        return create_engine(tmp_sqlite if is_linux else "sqlite:///./edupredict.db",
                             connect_args={"check_same_thread": False})


def _get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = _build_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_db():
    engine = _get_engine()
    if _SessionLocal is None:
        return
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and seed demo accounts if empty."""
    engine = _get_engine()

    from app import models  # noqa: F401 — registers all ORM models
    Base.metadata.create_all(bind=engine)

    db = _SessionLocal()
    try:
        from app.models import User, UserRole, Department, Section, Student, FacultyProfile, PortalDataset, Semester, SystemSetting
        from app.core.security import get_password_hash
        from app.data.students import PORTAL_DATASETS

        if db.query(User).first() is not None:
            return  # already seeded

        logger.info("Auto-seeding initial demo data…")

        # Admin
        admin = User(username="admin", hashed_password=get_password_hash("Admin@123"),
                     full_name="System Administrator", role=UserRole.ADMIN,
                     email="admin@edupredict.local", is_active=True)
        db.add(admin)

        # Departments
        dept_data = [("Computer Science & Engineering", "CSE"), ("Electronics & Communication", "ECE"),
                     ("Mechanical Engineering", "MECH"), ("Civil Engineering", "CIVIL"),
                     ("Information Technology", "IT")]
        dept_map = {}
        for name, code in dept_data:
            from app.models import Department as Dept
            d = Dept(name=name, code=code, description=f"{name} department")
            db.add(d)
            db.flush()
            dept_map[code] = d

        # Faculty
        for code, (uname, fname) in {"CSE": ("faculty", "Prof. CSE Faculty"),
                                      "ECE": ("faculty.ece", "Prof. ECE Faculty")}.items():
            fu = User(username=uname, hashed_password=get_password_hash("Faculty@123"),
                      full_name=fname, role=UserRole.FACULTY,
                      email=f"{uname}@edupredict.local", is_active=True)
            db.add(fu)
            db.flush()
            db.add(FacultyProfile(user_id=fu.id, employee_id=f"EMP{code}",
                                  department_id=dept_map[code].id, designation="Associate Professor"))

        # Section
        sec = Section(name="CSE-A", department_id=dept_map["CSE"].id,
                      academic_year="2025-2026", semester=1)
        db.add(sec)
        db.flush()

        # Meta
        db.add(Semester(name="Semester 1", semester=1, academic_year="2025-2026", is_current=True))
        db.add(SystemSetting(key="risk_low", value="0.39"))
        db.add(SystemSetting(key="risk_high", value="0.69"))

        # Portal demo students
        for ds in PORTAL_DATASETS:
            uname = (ds.get("username") or ds.get("studentId") or ds.get("rollNumber") or "").strip().lower()
            if not uname:
                continue
            name = ((ds.get("profile") or {}).get("name") or ds.get("name") or uname)
            su = User(username=uname, hashed_password=get_password_hash(ds.get("password") or "demo123"),
                      full_name=name, role=UserRole.STUDENT,
                      email=f"{uname}@student.edupredict.local", is_active=True)
            db.add(su)
            db.flush()
            st = Student(user_id=su.id, student_id=uname, section_id=sec.id,
                         admission_year=2023, current_semester=int(ds.get("currentSemester") or 5))
            db.add(st)
            db.flush()
            db.add(PortalDataset(student_id=st.id, data=json.dumps(ds)))

        db.commit()
        logger.info("Seeding complete.")
    except Exception as exc:
        db.rollback()
        logger.exception("Seeding error (non-fatal): %s", exc)
    finally:
        db.close()