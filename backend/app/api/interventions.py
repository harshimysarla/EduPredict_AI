from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_faculty_or_admin
from app.models import (
    User, UserRole, Student, Intervention, InterventionStatus,
    InterventionType, FacultyProfile, Section,
)
from app.schemas import InterventionCreate, InterventionUpdate, InterventionOut
from app.services.base import serialize_intervention, faculty_scope_filter

router = APIRouter(prefix="/interventions", tags=["interventions"])


def _faculty_for_user(db: Session, user: User):
    faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == user.id).first()
    if not faculty:
        raise HTTPException(status_code=400, detail="Faculty profile not found")
    return faculty


def _check_student_access(db: Session, student: Student, current_user: User) -> None:
    """Faculty/admins may only manage students within their authorized scope."""
    if current_user.role == UserRole.ADMIN:
        return
    faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
    if faculty is None:
        raise HTTPException(status_code=403, detail="Access denied")
    if student.section is None or student.section.department_id not in faculty_scope_filter(faculty):
        raise HTTPException(status_code=403, detail="Access denied to this student")


@router.post("", response_model=dict)
def create_intervention(
    data: InterventionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    _check_student_access(db, student, current_user)

    try:
        itype = InterventionType(data.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid intervention type: {data.type}")

    faculty = None
    if current_user.role == UserRole.FACULTY:
        faculty = _faculty_for_user(db, current_user)
    else:
        faculty = db.query(FacultyProfile).filter(
            FacultyProfile.department_id == student.section.department_id
        ).first() if student.section else db.query(FacultyProfile).first()
        if not faculty:
            raise HTTPException(status_code=400, detail="No faculty profile exists")

    intervention = Intervention(
        student_id=student.id,
        faculty_id=faculty.id,
        type=itype,
        title=data.title,
        description=data.description,
        follow_up_date=data.follow_up_date,
        notes=data.notes,
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    return {"id": intervention.id, **serialize_intervention(intervention)}


@router.get("", response_model=list[dict])
def list_interventions(
    student_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Intervention)
    if current_user.role == UserRole.STUDENT:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return []
        q = q.filter(Intervention.student_id == student.id)
    elif current_user.role == UserRole.FACULTY:
        faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
        if faculty:
            dept_ids = faculty_scope_filter(faculty)
            q = q.join(Student, Intervention.student_id == Student.id).join(
                Student.section
            ).filter(Section.department_id.in_(dept_ids))
    if student_id:
        q = q.filter(Intervention.student_id == student_id)
    if status:
        try:
            q = q.filter(Intervention.status == InterventionStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")

    interventions = q.order_by(Intervention.assigned_date.desc()).all()
    return [serialize_intervention(i) for i in interventions]


@router.put("/{intervention_id}", response_model=dict)
def update_intervention(
    intervention_id: int,
    data: InterventionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    intervention = db.query(Intervention).filter(Intervention.id == intervention_id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    if intervention.student:
        _check_student_access(db, intervention.student, current_user)

    if data.status:
        try:
            new_status = InterventionStatus(data.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
        intervention.status = new_status
        if new_status == InterventionStatus.COMPLETED:
            intervention.completed_date = datetime.utcnow()
    if data.notes is not None:
        intervention.notes = data.notes
    if data.follow_up_date:
        intervention.follow_up_date = data.follow_up_date

    db.commit()
    db.refresh(intervention)
    return serialize_intervention(intervention)