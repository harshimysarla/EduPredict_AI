from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.security import get_password_hash
from app.models import User, UserRole, Department, Section, Subject
from app.schemas import DepartmentOut, SectionOut, SubjectOut

router = APIRouter(prefix="/admin", tags=["admin"])


class DepartmentCreate(BaseModel):
    name: str
    code: str
    description: str | None = None


class SectionCreate(BaseModel):
    name: str
    department_id: int
    academic_year: str
    semester: int


class SubjectCreate(BaseModel):
    name: str
    code: str
    department_id: int
    credits: int = 3
    semester: int


class FacultyCreate(BaseModel):
    email: str
    password: str
    full_name: str
    employee_id: str
    department_id: int
    designation: str = "Assistant Professor"


@router.post("/departments", response_model=DepartmentOut, status_code=201)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    if db.query(Department).filter(Department.code == data.code).first():
        raise HTTPException(status_code=400, detail="Department code exists")
    dept = Department(name=data.name, code=data.code, description=data.description)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.post("/sections", response_model=SectionOut, status_code=201)
def create_section(
    data: SectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    dept = db.query(Department).filter(Department.id == data.department_id).first()
    if not dept:
        raise HTTPException(status_code=400, detail="Department not found")
    section = Section(
        name=data.name,
        department_id=data.department_id,
        academic_year=data.academic_year,
        semester=data.semester,
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


@router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(
    data: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    if db.query(Subject).filter(Subject.code == data.code).first():
        raise HTTPException(status_code=400, detail="Subject code exists")
    subject = Subject(
        name=data.name,
        code=data.code,
        department_id=data.department_id,
        credits=data.credits,
        semester=data.semester,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.post("/faculty", status_code=201)
def create_faculty(
    data: FacultyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    dept = db.query(Department).filter(Department.id == data.department_id).first()
    if not dept:
        raise HTTPException(status_code=400, detail="Department not found")
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    from app.services.base import create_faculty as cf

    faculty = cf(
        db, data.email, data.password, data.full_name,
        data.employee_id, dept, data.designation,
    )
    db.commit()
    return {
        "id": faculty.id,
        "employee_id": faculty.employee_id,
        "full_name": data.full_name,
        "email": data.email,
        "department_id": dept.id,
    }
