import json
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import (
    User, UserRole, Department, Section, Subject, Student, FacultyProfile,
    AcademicRecord, AttendanceRecord, EngagementRecord, Prediction, RiskLevel,
    Intervention, InterventionStatus, InterventionType, Notification,
    ModelVersion, Dataset,
)


def create_user(db: Session, email: str, password: str, full_name: str, role: UserRole) -> User:
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_department(db: Session, name: str, code: str) -> Department:
    dept = db.query(Department).filter(Department.code == code).first()
    if dept is None:
        dept = Department(name=name, code=code)
        db.add(dept)
        db.flush()
    return dept


def get_or_create_section(
    db: Session, name: str, department: Department, academic_year: str, semester: int
) -> Section:
    section = (
        db.query(Section)
        .filter(
            Section.name == name,
            Section.department_id == department.id,
            Section.academic_year == academic_year,
            Section.semester == semester,
        )
        .first()
    )
    if section is None:
        section = Section(
            name=name,
            department_id=department.id,
            academic_year=academic_year,
            semester=semester,
        )
        db.add(section)
        db.flush()
    return section


def get_or_create_subject(db: Session, name: str, code: str, department: Department, semester: int) -> Subject:
    subject = db.query(Subject).filter(Subject.code == code).first()
    if subject is None:
        subject = Subject(name=name, code=code, department_id=department.id, semester=semester, credits=3)
        db.add(subject)
        db.flush()
    return subject


def create_student(
    db: Session,
    student_id: str,
    full_name: str,
    email: str,
    password: str,
    section: Section,
    admission_year: int,
    current_semester: int = 1,
) -> Student:
    user = create_user(db, email, password, full_name, UserRole.STUDENT)
    student = Student(
        user_id=user.id,
        student_id=student_id,
        section_id=section.id,
        admission_year=admission_year,
        current_semester=current_semester,
    )
    db.add(student)
    db.flush()
    return student


def create_faculty(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    employee_id: str,
    department: Department,
    designation: str = "Assistant Professor",
) -> FacultyProfile:
    user = create_user(db, email, password, full_name, UserRole.FACULTY)
    faculty = FacultyProfile(
        user_id=user.id,
        employee_id=employee_id,
        department_id=department.id,
        designation=designation,
    )
    db.add(faculty)
    db.flush()
    return faculty


def notify(db: Session, user_id: int, title: str, message: str, ntype: str, related_id: Optional[int] = None):
    db.add(Notification(user_id=user_id, title=title, message=message, type=ntype, related_id=related_id))


def get_student_summary(db: Session, student: Student) -> dict:
    """Compute attendance, avg score, engagement, latest prediction for a student."""
    att = (
        db.query(func.avg(AttendanceRecord.attendance_percentage))
        .filter(AttendanceRecord.student_id == student.id)
        .scalar()
    )
    acad = (
        db.query(func.avg(AcademicRecord.total_score))
        .filter(AcademicRecord.student_id == student.id)
        .scalar()
    )
    eng = (
        db.query(func.avg(EngagementRecord.engagement_score))
        .filter(EngagementRecord.student_id == student.id)
        .scalar()
    )
    pred = (
        db.query(Prediction)
        .filter(Prediction.student_id == student.id)
        .order_by(Prediction.prediction_date.desc())
        .first()
    )
    return {
        "attendance": round(att, 2) if att is not None else None,
        "average_score": round(acad, 2) if acad is not None else None,
        "engagement": round(eng, 2) if eng is not None else None,
        "risk_probability": pred.risk_probability if pred else None,
        "risk_level": pred.risk_level.value if pred else None,
        "last_prediction": pred.prediction_date if pred else None,
    }


def latest_prediction_for(db: Session, student_id: int) -> Optional[Prediction]:
    return (
        db.query(Prediction)
        .filter(Prediction.student_id == student_id)
        .order_by(Prediction.prediction_date.desc())
        .first()
    )


def get_active_model(db: Session) -> Optional[ModelVersion]:
    return db.query(ModelVersion).filter(ModelVersion.is_active == True).first()  # noqa: E712


def serialize_intervention(i: Intervention) -> dict:
    return {
        "id": i.id,
        "student_id": i.student_id,
        "student_name": i.student.user.full_name if i.student else None,
        "student_id_str": i.student.student_id if i.student else None,
        "faculty_id": i.faculty_id,
        "faculty_name": i.faculty.user.full_name if i.faculty else None,
        "type": i.type.value,
        "title": i.title,
        "description": i.description,
        "status": i.status.value,
        "assigned_date": i.assigned_date,
        "follow_up_date": i.follow_up_date,
        "completed_date": i.completed_date,
        "notes": i.notes,
    }


def serialize_prediction(p: Prediction, student: Optional[Student] = None) -> dict:
    factors = []
    if p.feature_contributions:
        try:
            contrib = json.loads(p.feature_contributions)
            impacts = contrib.get("impacts", {})
            for f, v in contrib.get("contributions", {}).items():
                factors.append({"feature": f, "impact": impacts.get(f, "medium"), "value": v})
        except json.JSONDecodeError:
            pass

    recommendations = []
    if student is not None:
        try:
            from sqlalchemy import func
            from app.ml.pipeline import generate_recommendations
            db = Session.object_session(student)
            att = db.query(func.avg(AttendanceRecord.attendance_percentage)).filter(
                AttendanceRecord.student_id == student.id
            ).scalar()
            score = db.query(func.avg(AcademicRecord.total_score)).filter(
                AcademicRecord.student_id == student.id
            ).scalar()
            eng = db.query(func.avg(EngagementRecord.engagement_score)).filter(
                EngagementRecord.student_id == student.id
            ).scalar()
            recommendations = generate_recommendations(
                {
                    "attendance": float(att or 0),
                    "previous_performance": float(score or 0),
                    "internal_marks": float(score or 0),
                    "assignment_score": float(score or 0),
                    "engagement": float(eng or 0),
                    "study_hours": 0,
                },
                p.risk_level.value,
            )
        except Exception:
            recommendations = []

    return {
        "id": p.id,
        "student_id": student.student_id if student else p.student_id,
        "student_name": student.user.full_name if student else None,
        "risk_probability": p.risk_probability,
        "risk_level": p.risk_level.value,
        "model_name": p.model_name,
        "model_version": p.model_version,
        "prediction_date": p.prediction_date,
        "factors": factors,
        "recommendations": recommendations,
    }