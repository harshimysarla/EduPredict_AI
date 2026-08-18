"""Portal API: Samvidha-style academic performance data for students.

All endpoints read the student's OWN stored portal dataset (JSON seeded from
the local demo datasets or imported via CSV). Nothing here depends on the
real Samvidha site; a future college API only needs to supply the same shape.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User, UserRole, Student
from app.repositories.student_repository import get_portal_dataset
from app.services.attendance_service import attendance_analysis, semester_attendance, current_semester_attendance
from app.services.analytics_service import (
    cgpa_trend, semester_performance, credit_progress, subject_performance, pending_courses,
)
from app.services.performance_service import calculate_performance

router = APIRouter(tags=["portal"])

_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]


def _roman(sem: Optional[int]) -> Optional[str]:
    if sem is None or sem < 1 or sem > len(_ROMAN):
        return None
    return _ROMAN[sem - 1]


def _portal_data(db: Session, user: User) -> dict:
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Student access only")
    student = db.query(Student).filter(Student.user_id == user.id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student profile not found")
    data = get_portal_dataset(db, student)
    if data is None:
        raise HTTPException(status_code=404, detail="Portal data not available for this account")
    return data


def _profile(data: dict) -> dict:
    return data.get("profile") or {}


def _hero(data: dict, performance: dict) -> dict:
    profile = _profile(data)
    cur = profile.get("currentSemester") or data.get("currentSemester")
    credits = credit_progress(data)
    return {
        "name": profile.get("name"),
        "rollNumber": profile.get("rollNumber") or profile.get("studentId"),
        "section": profile.get("section"),
        "cgpa": profile.get("cgpa"),
        "currentSemester": cur,
        "currentSemesterLabel": _roman(cur) or f"Semester {cur}",
        "performanceIndex": performance["performanceIndex"],
        "attendance": current_semester_attendance(data),
        "creditsEarned": credits["completedCredits"],
        "programTotalCredits": credits["programTotalCredits"],
    }


@router.get("/student/me/portal/summary")
def portal_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Everything the student dashboard renders, computed from the portal data."""
    data = _portal_data(db, current_user)
    performance = calculate_performance(data)
    profile = _profile(data)
    return {
        "profile": profile,
        "placeholder": bool(data.get("placeholder")),
        "hero": _hero(data, performance),
        "academicOverview": {
            "cgpa": profile.get("cgpa"),
            "previousSgpa": profile.get("previousSgpa"),
            "previousSemesterCgpa": profile.get("previousSemesterCgpa"),
            "attendance": current_semester_attendance(data),
            "creditsEarned": credit_progress(data)["completedCredits"],
            "performanceIndex": performance["performanceIndex"],
        },
        "cgpaTrend": cgpa_trend(data),
        "semesterPerformance": semester_performance(data),
        "attendanceAnalysis": attendance_analysis(data),
        "subjects": subject_performance(data),
        "creditProgress": credit_progress(data),
        "pendingCourses": pending_courses(data),
        "currentSemesterCourses": data.get("currentSemesterCourses") or [],
        "performance": {
            "performanceIndex": performance["performanceIndex"],
            "academicScore": performance["academicScore"],
            "attendanceScore": performance["attendanceScore"],
            "internalScore": performance["internalScore"],
            "trendScore": performance["trendScore"],
            "creditCompletion": performance["creditCompletion"],
            "breakdown": performance["breakdown"],
            "weights": performance["weights"],
        },
        "strengths": performance["strengths"],
        "weaknesses": performance["weaknesses"],
        "risks": performance["risks"],
        "insights": performance["insights"],
    }


@router.get("/student/me/portal/profile")
def portal_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = _portal_data(db, current_user)
    performance = calculate_performance(data)
    return {
        **(_profile(data)),
        "username": current_user.username,
        "placeholder": bool(data.get("placeholder")),
        "performanceIndex": performance["performanceIndex"],
        "creditProgress": credit_progress(data),
    }


@router.get("/student/me/portal/semesters")
def portal_semesters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = _portal_data(db, current_user)
    return {
        "semesters": semester_performance(data),
        "currentSemester": (_profile(data).get("currentSemester") or data.get("currentSemester")) or 1,
    }


@router.get("/student/me/portal/semesters/{sem}")
def portal_semester_detail(
    sem: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = _portal_data(db, current_user)
    record = next(
        (s for s in (data.get("semesterRecords") or []) if s.get("semester") == sem),
        None,
    )
    if record is None:
        raise HTTPException(status_code=404, detail=f"Semester {sem} not found in records")
    profile = _profile(data)
    return {
        "semester": sem,
        "semesterLabel": _roman(sem) or f"Semester {sem}",
        "currentSemester": profile.get("currentSemester") or data.get("currentSemester"),
        "profile": profile,
        "theoryCourses": record.get("theoryCourses") or [],
        "labCourses": record.get("labCourses") or [],
        "attendance": semester_attendance(data, sem),
        "gradeRecords": record.get("gradeRecords") or [],
        "summary": record.get("semesterSummary") or {},
        "overallCgpa": profile.get("cgpa"),
    }


@router.get("/student/me/portal/subjects")
def portal_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    semester: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    course_type: Optional[str] = Query(None),
    sort_by: str = Query("semester"),
    order: str = Query("asc"),
):
    """Flattened subject list with search/filter/sort for the subjects table."""
    data = _portal_data(db, current_user)
    rows = subject_performance(data)
    if semester is not None:
        rows = [r for r in rows if r["semester"] == semester]
    if course_type:
        rows = [r for r in rows if (r.get("courseType") or "").upper() == course_type.upper()]
    if search:
        q = search.strip().lower()
        rows = [r for r in rows if q in (r.get("courseCode") or "").lower()
                or q in (r.get("courseName") or "").lower()]
    key = {
        "semester": lambda r: (r.get("semester") or 0),
        "courseCode": lambda r: (r.get("courseCode") or ""),
        "courseName": lambda r: (r.get("courseName") or ""),
        "grade": lambda r: (r.get("gradePoint") if r.get("gradePoint") is not None else -1),
        "attendance": lambda r: (r.get("attendance") if r.get("attendance") is not None else -1),
        "credits": lambda r: (r.get("credits") or 0),
    }.get(sort_by, lambda r: (r.get("semester") or 0))
    rows.sort(key=key, reverse=(order.lower() == "desc"))
    return {"subjects": rows, "total": len(rows)}


@router.post("/admin/portal/import")
async def admin_portal_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin-only CSV import into the portal dataset storage."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access only")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    from app.services.csv_import_service import parse_csv, import_datasets
    try:
        datasets = parse_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not datasets:
        raise HTTPException(status_code=400, detail="No valid student rows found in CSV")
    return import_datasets(db, datasets)