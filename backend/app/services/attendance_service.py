"""Attendance analysis for portal datasets.

Pure functions over the normalized student dataset (dict). No UI logic here.
"""
from typing import Optional


def _num(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def attendance_band(pct: Optional[float]) -> str:
    """Classify an attendance percentage for analysis."""
    if pct is None:
        return "Not Available"
    if pct >= 85:
        return "Excellent"
    if pct >= 75:
        return "Good"
    if pct >= 65:
        return "Risk"
    return "Critical"


def status_from_percentage(pct: Optional[float]) -> str:
    if pct is None:
        return "Not Available"
    if pct >= 75:
        return "Satisfactory"
    if pct >= 65:
        return "Condonation"
    return "Shortage"


def current_semester_attendance(dataset: dict) -> Optional[float]:
    """Average attendance % for the current (or most recent) semester."""
    courses = dataset.get("currentSemesterCourses") or []
    if not courses:
        courses = []
        for sem in dataset.get("semesterRecords") or []:
            for a in sem.get("attendance") or []:
                courses.append(a)
    vals = [_num(c.get("attendance") or c.get("attendancePercentage")) for c in courses]
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else None


def attendance_analysis(dataset: dict) -> list:
    """Per-course attendance for the current semester (portal attendance table)."""
    current = dataset.get("currentSemesterCourses") or []
    out = []
    for c in current:
        pct = _num(c.get("attendance") or c.get("attendancePercentage"))
        out.append({
            "courseCode": c.get("courseCode"),
            "courseName": c.get("courseName"),
            "courseType": c.get("courseType"),
            "courseCategory": c.get("courseCategory"),
            "conducted": c.get("conducted"),
            "attended": c.get("attended"),
            "attendancePercentage": pct,
            "status": c.get("status") or status_from_percentage(pct),
            "band": attendance_band(pct),
        })
    return out


def semester_attendance(dataset: dict, semester: int) -> list:
    """Attendance table for a specific semester from semesterRecords."""
    for sem in dataset.get("semesterRecords") or []:
        if sem.get("semester") == semester:
            return [
                {
                    **a,
                    "attendancePercentage": _num(a.get("attendancePercentage")),
                    "band": attendance_band(_num(a.get("attendancePercentage"))),
                }
                for a in sem.get("attendance") or []
            ]
    return []