from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import (
    User, UserRole, Department, Section, Subject, Student, FacultyProfile,
)
from app.schemas import DepartmentOut, SectionOut, SubjectOut, UserOut

router = APIRouter(tags=["meta"])


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Department).order_by(Department.name).all()


@router.get("/sections", response_model=list[SectionOut])
def list_sections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Section).order_by(Section.name).all()


@router.get("/subjects", response_model=list[SubjectOut])
def list_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Subject).order_by(Subject.name).all()


@router.get("/student/me")
def my_student_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Student access only")
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    from app.api.students import _to_out
    return _to_out(db, student)


@router.get("/student/me/academic-summary")
def my_academic_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Personalized academic dashboard data for the logged-in student,
    computed from THEIR OWN records via the active data provider."""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Student access only")
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    from app.services.base import build_academic_summary
    return build_academic_summary(db, student)


@router.get("/data-source")
def active_data_source(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models import DataSource
    from app.services.base import get_active_data_source
    src = get_active_data_source(db)
    samvidha = db.query(DataSource).filter(DataSource.type == "SAMVIDHA").first()
    return {
        **src,
        "samvidha_status": samvidha.status if samvidha else "NOT_CONFIGURED",
    }


@router.get("/faculty/me")
def my_faculty_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.FACULTY, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Faculty access only")
    faculty = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty profile not found")
    dept = db.query(Department).filter(Department.id == faculty.department_id).first()
    return {
        "employee_id": faculty.employee_id,
        "designation": faculty.designation,
        "department": dept.name if dept else None,
        "full_name": current_user.full_name,
        "email": current_user.email,
    }


@router.get("/mongodb/status")
def mongodb_status():
    from app.core.mongodb import check_mongo_status
    return check_mongo_status()