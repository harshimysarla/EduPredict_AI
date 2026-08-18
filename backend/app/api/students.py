from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles, get_faculty_or_admin
from app.models import (
    User, UserRole, Student, Section, Department, AcademicRecord, AttendanceRecord,
    EngagementRecord, Subject, FacultyProfile,
)
from app.schemas import (
    StudentCreate, StudentUpdate, StudentOut, AcademicRecordOut,
    AttendanceRecordOut, EngagementRecordOut, AcademicSummaryOut,
)
from app.services.base import (
    get_student_summary, create_student, build_academic_summary, faculty_scope_filter,
)

router = APIRouter(prefix="/students", tags=["students"])


def _to_out(db: Session, s: Student) -> StudentOut:
    summary = get_student_summary(db, s)
    section = db.query(Section).filter(Section.id == s.section_id).first()
    dept = db.query(Department).filter(Department.id == section.department_id).first() if section else None
    return StudentOut(
        id=s.id,
        student_id=s.student_id,
        full_name=s.user.full_name,
        email=s.user.email,
        section_id=s.section_id,
        section_name=section.name if section else None,
        department_name=dept.name if dept else None,
        admission_year=s.admission_year,
        current_semester=s.current_semester,
        is_active=s.is_active,
        **summary,
    )


def _load_student(db: Session, student_id: int) -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


def _check_access(db: Session, student: Student, current_user: User) -> None:
    """Authorization: students only their own data; faculty only their
    department's students; admins everything. Never leaks existence."""
    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.STUDENT:
        if student.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        return
    fp = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
    if fp is None:
        raise HTTPException(status_code=403, detail="Access denied")
    section = student.section
    if section is None or section.department_id not in faculty_scope_filter(fp):
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("", response_model=list[StudentOut])
def list_students(
    search: Optional[str] = None,
    risk: Optional[str] = None,
    section_id: Optional[int] = None,
    department_id: Optional[int] = None,
    semester: Optional[int] = None,
    subject_id: Optional[int] = None,
    year: Optional[int] = None,
    sort: Optional[str] = "risk_probability",
    order: Optional[str] = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    q = db.query(Student).join(Student.user)

    # Faculty scope: only students of the faculty member's department(s)
    if current_user.role == UserRole.FACULTY:
        fp = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
        if fp is None:
            return []
        dept_ids = faculty_scope_filter(fp)
        q = q.join(Section, Student.section_id == Section.id).filter(
            Section.department_id.in_(dept_ids)
        )

    if search:
        like = f"%{search}%"
        q = q.filter(or_(Student.student_id.ilike(like), User.full_name.ilike(like)))
    if section_id:
        q = q.filter(Student.section_id == section_id)
    if department_id:
        q = q.join(Section, Student.section_id == Section.id).filter(Section.department_id == department_id)
    if semester:
        q = q.filter(Student.current_semester == semester)
    if year:
        q = q.filter(Student.admission_year == year)
    if subject_id:
        q = q.join(AcademicRecord, AcademicRecord.student_id == Student.id).filter(
            AcademicRecord.subject_id == subject_id
        ).distinct()

    students = q.order_by(Student.id).all()

    from app.models import Prediction
    out_list = [_to_out(db, s) for s in students]

    if risk:
        out_list = [o for o in out_list if o.risk_level == risk]

    def sort_key(o: StudentOut):
        if sort == "attendance":
            return o.attendance if o.attendance is not None else -1
        if sort in ("average_score", "performance"):
            return o.average_score if o.average_score is not None else -1
        if sort == "engagement":
            return o.engagement if o.engagement is not None else -1
        return o.risk_probability if o.risk_probability is not None else -1

    out_list.sort(key=sort_key, reverse=(order == "desc"))

    total = len(out_list)
    start = (page - 1) * page_size
    items = out_list[start : start + page_size]
    # Include total via response header for pagination
    items_ = items
    return items_


@router.get("/{student_id}/academic-summary", response_model=AcademicSummaryOut)
def academic_summary(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = _load_student(db, student_id)
    _check_access(db, student, current_user)
    return build_academic_summary(db, student)


@router.post("", response_model=StudentOut, status_code=201)
def add_student(
    data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    section = db.query(Section).filter(Section.id == data.section_id).first()
    if not section:
        raise HTTPException(status_code=400, detail="Section not found")
    if db.query(Student).filter(Student.student_id == data.student_id).first():
        raise HTTPException(status_code=400, detail="Student ID already exists")
    if db.query(User).filter(User.username == data.username.lower()).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    student = create_student(
        db, data.student_id, data.full_name, data.username, data.password,
        section, data.admission_year, data.current_semester, email=data.email,
    )
    db.commit()
    db.refresh(student)
    return _to_out(db, student)


@router.get("/{student_id}", response_model=StudentOut)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = _load_student(db, student_id)
    _check_access(db, student, current_user)
    return _to_out(db, student)


@router.put("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    student = _load_student(db, student_id)

    if data.full_name:
        student.user.full_name = data.full_name
    if data.email:
        student.user.email = data.email
    if data.section_id:
        student.section_id = data.section_id
    if data.admission_year:
        student.admission_year = data.admission_year
    if data.current_semester:
        student.current_semester = data.current_semester
    if data.is_active is not None:
        student.is_active = data.is_active
        student.user.is_active = data.is_active

    db.commit()
    db.refresh(student)
    return _to_out(db, student)


@router.get("/{student_id}/performance", response_model=list[AcademicRecordOut])
def student_performance(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = _load_student(db, student_id)
    _check_access(db, student, current_user)

    records = (
        db.query(AcademicRecord)
        .filter(AcademicRecord.student_id == student_id)
        .order_by(AcademicRecord.semester, AcademicRecord.subject_id)
        .all()
    )
    result = []
    for r in records:
        subject = db.query(Subject).filter(Subject.id == r.subject_id).first()
        result.append(
            AcademicRecordOut(
                id=r.id, subject_id=r.subject_id,
                subject_name=subject.name if subject else None,
                semester=r.semester, internal_marks=r.internal_marks,
                assignment_score=r.assignment_score, exam_score=r.exam_score,
                total_score=r.total_score, grade=r.grade,
            )
        )
    return result


@router.get("/{student_id}/attendance", response_model=list[AttendanceRecordOut])
def student_attendance(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = _load_student(db, student_id)
    _check_access(db, student, current_user)

    records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student_id)
        .order_by(AttendanceRecord.semester, AttendanceRecord.month)
        .all()
    )
    result = []
    for r in records:
        subject = db.query(Subject).filter(Subject.id == r.subject_id).first()
        result.append(
            AttendanceRecordOut(
                id=r.id, subject_id=r.subject_id,
                subject_name=subject.name if subject else None,
                semester=r.semester, month=r.month,
                classes_held=r.classes_held, classes_attended=r.classes_attended,
                attendance_percentage=r.attendance_percentage,
            )
        )
    return result


@router.get("/{student_id}/engagement", response_model=list[EngagementRecordOut])
def student_engagement(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = _load_student(db, student_id)
    _check_access(db, student, current_user)

    records = (
        db.query(EngagementRecord)
        .filter(EngagementRecord.student_id == student_id)
        .order_by(EngagementRecord.semester, EngagementRecord.month)
        .all()
    )
    return [EngagementRecordOut.model_validate(r) for r in records]