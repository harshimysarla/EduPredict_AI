"""Abstract academic data provider contract + data source management.

Every provider exposes the same surface so the application never depends on a
specific data source. Providers read/write through the application database;
they differ in provenance (demo seed vs CSV import vs future official API).
"""
from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.orm import Session

from app.models import DataSource, Student


class ProviderNotConfigured(Exception):
    """Raised when a provider is not configured (e.g. Samvidha)."""


class AcademicDataProvider(ABC):
    type: str = "DEMO"
    display_name: str = "Demo Dataset"

    def __init__(self, db: Session):
        self.db = db

    # ----- data source metadata -------------------------------------------------
    def source(self) -> Optional[DataSource]:
        return (
            self.db.query(DataSource)
            .filter(DataSource.type == self.type)
            .first()
        )

    # ----- student / academic data ---------------------------------------------
    @abstractmethod
    def get_student_profile(self, student_id: int) -> Optional[Student]:
        ...

    def get_attendance(self, student_id: int, semester: Optional[int] = None) -> list:
        from app.models import AttendanceRecord
        q = self.db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student_id)
        if semester is not None:
            q = q.filter(AttendanceRecord.semester == semester)
        return q.order_by(AttendanceRecord.semester, AttendanceRecord.month).all()

    def get_academic_records(self, student_id: int, semester: Optional[int] = None) -> list:
        from app.models import AcademicRecord
        q = self.db.query(AcademicRecord).filter(AcademicRecord.student_id == student_id)
        if semester is not None:
            q = q.filter(AcademicRecord.semester == semester)
        return q.order_by(AcademicRecord.semester).all()

    def get_assessment_records(self, student_id: int, semester: Optional[int] = None) -> list:
        from app.models import AssessmentRecord
        q = self.db.query(AssessmentRecord).filter(AssessmentRecord.student_id == student_id)
        if semester is not None:
            q = q.filter(AssessmentRecord.semester == semester)
        return q.order_by(AssessmentRecord.semester, AssessmentRecord.assessment_number).all()

    def get_assignment_records(self, student_id: int, semester: Optional[int] = None) -> list:
        from app.models import AssignmentRecord
        q = self.db.query(AssignmentRecord).filter(AssignmentRecord.student_id == student_id)
        if semester is not None:
            q = q.filter(AssignmentRecord.semester == semester)
        return q.order_by(AssignmentRecord.semester).all()

    def get_engagement(self, student_id: int, semester: Optional[int] = None) -> list:
        from app.models import EngagementRecord
        q = self.db.query(EngagementRecord).filter(EngagementRecord.student_id == student_id)
        if semester is not None:
            q = q.filter(EngagementRecord.semester == semester)
        return q.order_by(EngagementRecord.semester, EngagementRecord.month).all()

    def get_performance_history(self, student_id: int) -> list:
        """Ordered (semester, assessment) performance trend from database records."""
        history = []
        for r in self.get_assessment_records(student_id):
            history.append({
                "semester": r.semester,
                "label": f"Internal {r.assessment_number}",
                "score": r.marks,
            })
        for r in self.get_academic_records(student_id):
            if r.total_score is not None:
                history.append({
                    "semester": r.semester,
                    "label": r.subject.name if r.subject else "Overall",
                    "score": r.total_score,
                })
        history.sort(key=lambda h: (h["semester"], h["label"]))
        return history

    def get_class_students(self, faculty_user) -> list:
        """Students the given faculty user is authorized to manage.

        Default scope: students in the faculty member's department sections.
        Admins see every student.
        """
        from app.models import FacultyProfile, UserRole
        if faculty_user.role == UserRole.ADMIN:
            return self.db.query(Student).all()
        fp = self.db.query(FacultyProfile).filter(FacultyProfile.user_id == faculty_user.id).first()
        if fp is None:
            return []
        from app.models import Department, Section
        dept_ids = [fp.department_id]
        if fp.section_id:
            sec = self.db.query(Section).filter(Section.id == fp.section_id).first()
            if sec:
                dept_ids.append(sec.department_id)
        dept_ids = list(set(dept_ids))
        return (
            self.db.query(Student)
            .join(Section, Student.section_id == Section.id)
            .filter(Section.department_id.in_(dept_ids))
            .all()
        )


# ----- data source management ---------------------------------------------------


def ensure_default_sources(db: Session) -> None:
    defaults = [
        ("Demo Dataset", "DEMO", "ACTIVE",
         "Synthetic academic records generated locally for development and demos."),
        ("Approved Academic Import", "CSV", "AVAILABLE",
         "Academic records imported from an approved CSV/Excel export."),
        ("IARE Samvidha Integration", "SAMVIDHA", "NOT_CONFIGURED",
         "Official IARE/Samvidha API integration. Requires official credentials "
         "and API documentation. EduPredict is NOT connected to Samvidha."),
    ]
    for name, stype, status, desc in defaults:
        row = db.query(DataSource).filter(DataSource.type == stype).first()
        if row is None:
            db.add(DataSource(name=name, type=stype, status=status, description=desc))
    db.commit()


def list_data_sources(db: Session) -> list:
    ensure_default_sources(db)
    return db.query(DataSource).order_by(DataSource.id).all()


def get_active_provider(db: Session):
    from app.providers import PROVIDER_BY_TYPE
    ensure_default_sources(db)
    src = db.query(DataSource).filter(DataSource.status == "ACTIVE").first()
    stype = src.type if src else "DEMO"
    return PROVIDER_BY_TYPE[stype](db)


def activate_data_source(db: Session, source_type: str):
    """Activate a data source. Returns the source or raises ProviderNotConfigured."""
    from app.providers import PROVIDER_BY_TYPE
    ensure_default_sources(db)
    src = db.query(DataSource).filter(DataSource.type == source_type.upper()).first()
    if src is None:
        raise ValueError(f"Unknown data source type: {source_type}")
    if src.status == "NOT_CONFIGURED":
        raise ProviderNotConfigured(
            f"{src.name} is not configured. An official API and credentials are required."
        )
    for other in db.query(DataSource).filter(DataSource.status == "ACTIVE").all():
        other.status = "AVAILABLE"
    src.status = "ACTIVE"
    db.commit()
    return src