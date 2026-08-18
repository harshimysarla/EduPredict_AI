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
    username: str
    password: str
    full_name: str
    employee_id: str
    department_id: int
    designation: str = "Assistant Professor"
    email: str | None = None


class SettingUpdate(BaseModel):
    key: str | None = None
    value: str


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
    if db.query(User).filter(User.username == data.username.lower()).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    from app.services.base import create_faculty as cf

    faculty = cf(
        db, data.username, data.password, data.full_name,
        data.employee_id, dept, data.designation, email=data.email,
    )
    db.commit()
    return {
        "id": faculty.id,
        "employee_id": faculty.employee_id,
        "full_name": data.full_name,
        "username": data.username,
        "email": data.email,
        "department_id": dept.id,
    }


# ----- Data source management -----------------------------------------------------


@router.get("/data-sources")
def data_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    from app.providers import list_data_sources, PROVIDER_BY_TYPE

    sources = list_data_sources(db)
    result = []
    for s in sources:
        provider_cls = PROVIDER_BY_TYPE.get(s.type)
        item = {
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "status": s.status,
            "description": s.description,
            "last_synced_at": s.last_synced_at,
            "record_count": s.record_count,
        }
        if provider_cls is not None:
            provider = provider_cls(db)
            item["record_count"] = provider.source().record_count if provider.source() else None
        result.append(item)
    return result


@router.post("/data-sources/{source_type}/activate")
def activate_source(
    source_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    from app.providers import activate_data_source, ProviderNotConfigured

    try:
        src = activate_data_source(db, source_type)
    except ProviderNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "id": src.id,
        "name": src.name,
        "type": src.type,
        "status": src.status,
        "record_count": src.record_count,
        "last_synced_at": src.last_synced_at,
    }


# ----- System settings (risk thresholds etc.) -------------------------------------


@router.get("/settings")
def list_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    from app.models import SystemSetting
    defaults = {"risk_low": "0.39", "risk_high": "0.69"}
    rows = {s.key: s.value for s in db.query(SystemSetting).all()}
    for k, v in defaults.items():
        rows.setdefault(k, v)
    return [{"key": k, "value": v} for k, v in sorted(rows.items())]


@router.put("/settings/{key}")
def update_setting(
    key: str,
    data: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    from app.models import SystemSetting

    allowed = {"risk_low", "risk_high"}
    if key not in allowed:
        raise HTTPException(status_code=400, detail="Unknown setting")
    try:
        value = float(data.value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Value must be numeric")
    if not (0 < value < 1):
        raise HTTPException(status_code=400, detail="Value must be between 0 and 1")

    current = {s.key: s.value for s in db.query(SystemSetting).all()}
    other_key = "risk_high" if key == "risk_low" else "risk_low"
    other = float(current.get(other_key, 0.69 if key == "risk_low" else 0.39))
    if key == "risk_low" and value >= other:
        raise HTTPException(status_code=400, detail="risk_low must be below risk_high")
    if key == "risk_high" and value <= other:
        raise HTTPException(status_code=400, detail="risk_high must be above risk_low")

    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if setting is None:
        setting = SystemSetting(key=key, value=str(value))
        db.add(setting)
    else:
        setting.value = str(value)
    db.commit()
    return {"key": key, "value": str(value)}
