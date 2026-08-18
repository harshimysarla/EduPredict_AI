import json
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.schemas import SubjectAnalysis
from app.models import (
    User, UserRole, Department, Section, Subject, Student, FacultyProfile,
    AcademicRecord, AttendanceRecord, EngagementRecord, AssessmentRecord,
    AssignmentRecord, Prediction, RiskLevel,
    Intervention, InterventionStatus, InterventionType, Notification,
    ModelVersion, Dataset,
)


def create_user(db: Session, username: str, password: str, full_name: str, role: UserRole,
                email: Optional[str] = None) -> User:
    user = User(
        username=username.strip().lower(),
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
    username: str,
    password: str,
    section: Section,
    admission_year: int,
    current_semester: int = 1,
    email: Optional[str] = None,
) -> Student:
    user = create_user(db, username, password, full_name, UserRole.STUDENT, email=email)
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
    username: str,
    password: str,
    full_name: str,
    employee_id: str,
    department: Department,
    designation: str = "Assistant Professor",
    email: Optional[str] = None,
) -> FacultyProfile:
    user = create_user(db, username, password, full_name, UserRole.FACULTY, email=email)
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


def get_risk_thresholds(db: Session) -> dict:
    """Risk thresholds configurable by admin (system_settings), with fallbacks."""
    from app.models import SystemSetting
    settings_rows = {s.key: s.value for s in db.query(SystemSetting).all()}
    defaults = {"low": 0.39, "high": 0.69}
    try:
        low = float(settings_rows.get("risk_low", defaults["low"]))
        high = float(settings_rows.get("risk_high", defaults["high"]))
    except (TypeError, ValueError):
        low, high = defaults["low"], defaults["high"]
    if low <= 0 or high <= low or high >= 1:
        low, high = defaults["low"], defaults["high"]
    return {"low": low, "high": high}


def get_active_data_source(db: Session) -> Optional[dict]:
    from app.models import DataSource
    src = db.query(DataSource).filter(DataSource.status == "ACTIVE").first()
    if src is None:
        return {"name": "Demo Dataset", "type": "DEMO", "status": "ACTIVE",
                "record_count": 0, "last_synced_at": None}
    return {
        "id": src.id, "name": src.name, "type": src.type, "status": src.status,
        "record_count": src.record_count, "last_synced_at": src.last_synced_at,
    }


def faculty_scope_filter(faculty_profile) -> list:
    """Department ids a faculty member is authorized to manage."""
    ids = [faculty_profile.department_id]
    if faculty_profile.section_id:
        ids.append(faculty_profile.section.department_id)
    return list(set(ids))


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
def serialize_student_profile(student: Student) -> dict:
    """Profile for a student, derived from database records (never hardcoded)."""
    section = student.section
    dept = section.department if section else None
    return {
        "student_id": student.student_id,
        "full_name": student.user.full_name if student.user else None,
        "department": dept.name if dept else None,
        "department_code": dept.code if dept else None,
        "section": section.name if section else None,
        "year": student.admission_year,
        "semester": student.current_semester,
        "academic_year": section.academic_year if section else None,
        "admission_year": student.admission_year,
        "username": student.user.username if student.user else None,
    }


def build_academic_summary(db: Session, student: Student, provider=None, thresholds: Optional[dict] = None) -> dict:
    """Personalized academic summary computed from the student's own database records
    through the active AcademicDataProvider."""
    from app.ml.pipeline import compute_student_features, risk_level_from_probability, generate_recommendations

    if provider is None:
        from app.providers import get_active_provider
        provider = get_active_provider(db)

    att = db.query(func.avg(AttendanceRecord.attendance_percentage)).filter(
        AttendanceRecord.student_id == student.id).scalar()
    acad = db.query(func.avg(AcademicRecord.total_score)).filter(
        AcademicRecord.student_id == student.id).scalar()
    eng = db.query(func.avg(EngagementRecord.engagement_score)).filter(
        EngagementRecord.student_id == student.id).scalar()
    i1 = db.query(func.avg(AssessmentRecord.marks)).filter(
        AssessmentRecord.student_id == student.id,
        AssessmentRecord.assessment_number == 1).scalar()
    i2 = db.query(func.avg(AssessmentRecord.marks)).filter(
        AssessmentRecord.student_id == student.id,
        AssessmentRecord.assessment_number == 2).scalar()
    assign = db.query(func.avg(AssignmentRecord.completion_percentage)).filter(
        AssignmentRecord.student_id == student.id).scalar()
    if assign is None:
        assign = db.query(func.avg(AssignmentRecord.score)).filter(
            AssignmentRecord.student_id == student.id).scalar()

    features = compute_student_features(db, student.id)
    latest_pred = latest_prediction_for(db, student.id)
    if latest_pred is not None:
        risk_probability = latest_pred.risk_probability
        risk_level = latest_pred.risk_level.value
        model_name = latest_pred.model_name
    else:
        risk_probability = None
        risk_level = None
        model_name = None

    # subject-wise analysis from actual records
    subjects_out = []
    subject_rows = (
        db.query(AcademicRecord, func.avg(AttendanceRecord.attendance_percentage), func.avg(AssignmentRecord.completion_percentage))
        .outerjoin(AttendanceRecord, (AttendanceRecord.student_id == AcademicRecord.student_id)
                   & (AttendanceRecord.subject_id == AcademicRecord.subject_id)
                   & (AttendanceRecord.semester == AcademicRecord.semester))
        .outerjoin(AssignmentRecord, (AssignmentRecord.student_id == AcademicRecord.student_id)
                   & (AssignmentRecord.subject_id == AcademicRecord.subject_id)
                   & (AssignmentRecord.semester == AcademicRecord.semester))
        .filter(AcademicRecord.student_id == student.id)
        .group_by(AcademicRecord.id)
        .all()
    )
    for rec, subj_att, subj_assign in subject_rows:
        trend = "stable"
        sem_recs = [r for r in student.academic_records if r.subject_id == rec.subject_id]
        if len(sem_recs) >= 2:
            prev_total = sem_recs[-2].total_score
            cur_total = sem_recs[-1].total_score
            if prev_total is not None and cur_total is not None:
                if cur_total - prev_total > 3:
                    trend = "up"
                elif prev_total - cur_total > 3:
                    trend = "down"
        subjects_out.append(SubjectAnalysis(
            subject_id=rec.subject_id,
            subject_name=rec.subject.name if rec.subject else None,
            subject_code=rec.subject.code if rec.subject else None,
            attendance=round(subj_att, 1) if subj_att is not None else None,
            internal_marks=rec.internal_marks,
            assignment_score=rec.assignment_score,
            total_score=rec.total_score,
            grade=rec.grade,
            trend=trend,
        ))

    health = {
        "overall_performance": round(acad, 1) if acad is not None else None,
        "attendance": round(att, 1) if att is not None else None,
        "engagement": round(eng, 1) if eng is not None else None,
        "internal_1": round(i1, 1) if i1 is not None else None,
        "internal_2": round(i2, 1) if i2 is not None else None,
        "internal_average": round(((i1 or 0) + (i2 or 0)) / 2, 1) if (i1 is not None or i2 is not None) else None,
        "assignment_completion": round(assign, 1) if assign is not None else None,
    }

    recommendations = []
    if features is not None:
        recommendations = generate_recommendations(features, risk_level or "low",
                                                   thresholds=thresholds)

    performance_history = [
        {"label": f"Internal {r.assessment_number}", "score": r.marks, "semester": r.semester}
        for r in provider.get_assessment_records(student.id)
    ]
    for r in provider.get_academic_records(student.id):
        if r.total_score is not None:
            performance_history.append({"label": r.subject.name if r.subject else "Overall",
                                        "score": r.total_score, "semester": r.semester})
    performance_history.sort(key=lambda h: (h.get("semester", 0), h["label"]))

    src = get_active_data_source(db)
    return {
        "profile": serialize_student_profile(student),
        "health": health,
        "subjects": [s.model_dump() for s in subjects_out],
        "performance_history": performance_history,
        "risk": {
            "risk_probability": round(risk_probability, 4) if risk_probability is not None else None,
            "risk_level": risk_level,
            "model_name": model_name,
            "thresholds": thresholds or get_risk_thresholds(db),
        },
        "recommendations": recommendations,
        "data_source": src,
    }
