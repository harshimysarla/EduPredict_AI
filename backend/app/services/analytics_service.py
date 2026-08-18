"""Analytics helpers over the normalized portal dataset."""
from typing import Optional


def _num(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def cgpa_trend(dataset: dict) -> list:
    """[{semester, sgpa, cgpa, label}] for completed semesters + placeholders."""
    records = sorted(
        (s for s in dataset.get("semesterRecords") or []),
        key=lambda s: s.get("semester") or 0,
    )
    trend = []
    cumulative_points = 0.0
    cumulative_credits = 0
    for sem in records:
        summary = sem.get("semesterSummary") or {}
        sgpa = _num(summary.get("sgpa"))
        total_credits = int(summary.get("totalCredits") or 0)
        if sgpa is not None:
            cumulative_points += sgpa * total_credits
            cumulative_credits += total_credits
            cgpa = round(cumulative_points / cumulative_credits, 2) if cumulative_credits else None
        else:
            cgpa = None
        trend.append({
            "semester": sem.get("semester"),
            "label": f"Semester {sem.get('semester')}",
            "sgpa": sgpa,
            "cgpa": cgpa,
            "completed": sgpa is not None,
        })
    return trend


def semester_performance(dataset: dict) -> list:
    return [
        {
            "semester": s.get("semester"),
            "sgpa": _num((s.get("semesterSummary") or {}).get("sgpa")),
            "totalCredits": (s.get("semesterSummary") or {}).get("totalCredits"),
            "earnedCredits": (s.get("semesterSummary") or {}).get("earnedCredits"),
        }
        for s in sorted(dataset.get("semesterRecords") or [], key=lambda x: x.get("semester") or 0)
    ]


def credit_progress(dataset: dict) -> dict:
    overall = dataset.get("overallSummary") or {}
    earned = int(overall.get("earnedCredits") or 0)
    program_total = int(overall.get("programTotalCredits") or 0)
    if program_total <= 0:
        program_total = earned
    return {
        "completedCredits": earned,
        "remainingCredits": max(0, program_total - earned),
        "completionPercent": round(earned / program_total * 100, 1) if program_total else 0,
        "programTotalCredits": program_total,
    }


def _all_courses(dataset: dict) -> list:
    """Flatten all theory+lab courses across semesters into one list."""
    rows = []
    for sem in dataset.get("semesterRecords") or []:
        sem_no = sem.get("semester")
        for t in sem.get("theoryCourses") or []:
            rows.append({**t, "semester": sem_no, "type": "Theory"})
        for l in sem.get("labCourses") or []:
            rows.append({**l, "semester": sem_no, "type": "Laboratory"})
    return rows


def subject_performance(dataset: dict) -> list:
    """Every course across semesters, normalized for the subject table."""
    rows = []
    for c in _all_courses(dataset):
        rows.append({
            "semester": c.get("semester"),
            "courseCode": c.get("courseCode"),
            "courseName": c.get("courseName"),
            "courseType": c.get("courseType"),
            "courseCategory": c.get("courseCategory"),
            "credits": c.get("credits"),
            "grade": c.get("grade"),
            "gradePoint": c.get("gradePoint"),
            "totalMarks": _num(c.get("totalMarks")),
            "attendance": _num(c.get("attendance")),
            "status": c.get("status"),
            "type": c.get("type"),
        })
    return rows


def pending_courses(dataset: dict) -> list:
    return dataset.get("coursesDue") or []