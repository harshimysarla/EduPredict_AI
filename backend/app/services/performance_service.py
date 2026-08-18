"""Central performance calculation engine.

All dashboard numbers are derived HERE from the student's dataset. Weights are
configurable in one place (PI_WEIGHTS). The UI only renders what this returns.
"""
from typing import Optional

from app.services.attendance_service import current_semester_attendance, status_from_percentage
from app.services.analytics_service import cgpa_trend, credit_progress, semester_performance, subject_performance

# Configurable Performance Index weights (sums to 1.0).
PI_WEIGHTS = {
    "academic": 0.40,     # credit-weighted grade performance
    "attendance": 0.20,   # current semester attendance
    "internal": 0.20,     # internal assessment marks (CIE + AAT)
    "trend": 0.10,        # SGPA trend across completed semesters
    "completion": 0.10,   # credit completion rate
}


def _num(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def academic_score(dataset: dict) -> float:
    """Credit-weighted average gradePoint over completed credited courses -> 0..100."""
    points = 0.0
    credits = 0.0
    for sem in dataset.get("semesterRecords") or []:
        for c in sem.get("gradeRecords") or []:
            gp = _num(c.get("gradePoint"))
            cr = _num(c.get("credits")) or 0
            if gp is not None and cr > 0 and c.get("status") in (None, "Completed", "completed"):
                points += gp * cr
                credits += cr
    if credits <= 0:
        return 0.0
    return round(points / credits / 10 * 100, 2)


def internal_score(dataset: dict) -> Optional[float]:
    """Average internal assessment totalMarks (%) across courses with marks."""
    vals = []
    for sem in dataset.get("semesterRecords") or []:
        for c in sem.get("theoryCourses") or []:
            tm = _num(c.get("totalMarks"))
            if tm is not None:
                vals.append(tm)
    return round(sum(vals) / len(vals), 2) if vals else None


def trend_score(dataset: dict) -> float:
    """SGPA movement across completed semesters, mapped to 0..100."""
    sems = [s for s in semester_performance(dataset) if s.get("sgpa") is not None]
    if len(sems) < 2:
        return 65.0
    last = sems[-1]["sgpa"]
    prev = sems[-2]["sgpa"]
    delta = last - prev
    return round(_clamp(65 + delta * 50), 2)


def attendance_score(dataset: dict) -> Optional[float]:
    return current_semester_attendance(dataset)


def _completed_courses(dataset: dict) -> list:
    return subject_performance(dataset)


def calculate_performance(dataset: dict) -> dict:
    """Full performance analysis for one student dataset."""
    acad = academic_score(dataset)
    att = attendance_score(dataset)
    intern = internal_score(dataset)
    trend = trend_score(dataset)
    credits = credit_progress(dataset)

    completion = credits["completionPercent"]
    att_score = att if att is not None else acad  # fall back when no attendance

    index = round(
        PI_WEIGHTS["academic"] * acad
        + PI_WEIGHTS["attendance"] * att_score
        + PI_WEIGHTS["internal"] * (intern if intern is not None else acad)
        + PI_WEIGHTS["trend"] * trend
        + PI_WEIGHTS["completion"] * completion,
        1,
    )

    strengths, weaknesses, risks = _diagnose(dataset)
    insights = _insights(dataset, acad, att, intern, index)

    return {
        "performanceIndex": index,
        "academicScore": round(acad, 2),
        "attendanceScore": att,
        "internalScore": intern,
        "gradeScore": round(acad, 2),
        "trendScore": trend,
        "creditCompletion": completion,
        "weights": PI_WEIGHTS,
        "breakdown": {
            "academic": round(acad, 2),
            "attendance": att_score,
            "internal": intern if intern is not None else round(acad, 2),
            "trend": trend,
            "completion": completion,
        },
        "strengths": strengths,
        "weaknesses": weaknesses,
        "risks": risks,
        "insights": insights,
    }


def _diagnose(dataset: dict):
    courses = _completed_courses(dataset)
    current = dataset.get("currentSemesterCourses") or []

    # Strengths: highest credit-weighted gradePoint courses
    graded = [c for c in courses if c.get("gradePoint") is not None]
    graded.sort(key=lambda c: (c["gradePoint"] or 0) * (c.get("credits") or 0), reverse=True)
    strengths = []
    if graded:
        top = graded[0]
        strengths.append({
            "label": "Strongest Area",
            "courseCode": top["courseCode"],
            "courseName": top["courseName"],
            "detail": f"Grade {top['grade']} ({top['gradePoint']} grade points)",
        })
    labs = [c for c in graded if c.get("courseType") == "L" or c.get("type") == "Laboratory"]
    if labs:
        avg_lab_gp = round(sum(c["gradePoint"] for c in labs) / len(labs), 2)
        if avg_lab_gp >= 8:
            strengths.append({
                "label": "Consistent Performance",
                "courseCode": None,
                "courseName": "Programming & Laboratory Courses",
                "detail": f"Average grade point {avg_lab_gp:.2f} across {len(labs)} practical courses",
            })
    cats = {}
    for c in graded:
        key = c.get("courseCategory") or "OTHER"
        cats.setdefault(key, []).append(c["gradePoint"])
    best_cat = max(cats.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
    if best_cat[0] not in ("CORE", "SKILL"):
        avg_cat = sum(best_cat[1]) / len(best_cat[1])
        if avg_cat >= 8:
            strengths.append({
                "label": "Subject Area Strength",
                "courseCode": None,
                "courseName": best_cat[0].replace("_", " ").title(),
                "detail": f"Average grade point {avg_cat:.2f}",
            })

    # Weaknesses: low gradePoint courses + low attendance
    weaknesses = []
    weak_graded = [c for c in graded if (c.get("gradePoint") or 0) <= 7]
    weak_graded.sort(key=lambda c: c["gradePoint"])
    for c in weak_graded[:3]:
        weaknesses.append({
            "label": "Lower Grade",
            "courseCode": c["courseCode"],
            "courseName": c["courseName"],
            "detail": f"Grade {c['grade']} ({c['gradePoint']} grade points)",
            "value": c["gradePoint"],
        })

    # Risks: attendance + academic
    risks = []
    for c in current:
        pct = _num(c.get("attendance") or c.get("attendancePercentage"))
        if pct is not None and pct < 75:
            risks.append({
                "category": "Attendance Risk",
                "courseCode": c.get("courseCode"),
                "courseName": c.get("courseName"),
                "metric": "attendance",
                "value": pct,
                "detail": f"Attendance {pct:.2f}% — {status_from_percentage(pct)}",
            })
    trend = cgpa_trend(dataset)
    completed = [t for t in trend if t.get("completed")]
    if len(completed) >= 2 and completed[-1]["sgpa"] < completed[-2]["sgpa"]:
        risks.append({
            "category": "Academic Risk",
            "courseCode": None,
            "courseName": f"Semester {completed[-1]['semester']}",
            "metric": "sgpa_decline",
            "value": completed[-2]["sgpa"] - completed[-1]["sgpa"],
            "detail": f"SGPA declined from {completed[-2]['sgpa']} to {completed[-1]['sgpa']}",
        })
    return strengths, weaknesses, risks


def _insights(dataset: dict, acad: float, att: Optional[float], intern: Optional[float], index: float) -> list:
    insights = []
    profile = dataset.get("profile") or {}
    cgpa = _num(profile.get("cgpa"))
    name = profile.get("name") or ""

    if cgpa is not None:
        if cgpa >= 8.5:
            insights.append({
                "severity": "positive",
                "title": "Strong overall performance",
                "message": f"Your CGPA is {cgpa:.2f}, indicating strong academic performance.",
            })
        elif cgpa < 6.5:
            insights.append({
                "severity": "warning",
                "title": "Academic performance needs attention",
                "message": f"Your CGPA of {cgpa:.2f} is below the strong-performance band. "
                           "Focus on the subjects with the lowest grades.",
            })
    if index >= 80:
        insights.append({
            "severity": "positive",
            "title": "High performance index",
            "message": f"Your performance index of {index} reflects consistently good academics.",
        })
    if att is not None and att < 75:
        insights.append({
            "severity": "warning",
            "title": "Attendance below satisfactory threshold",
            "message": f"Current attendance is {att:.1f}%. Courses below 75% may require condonation.",
        })
    for c in dataset.get("currentSemesterCourses") or []:
        pct = _num(c.get("attendance") or c.get("attendancePercentage"))
        if pct is not None and pct < 75:
            insights.append({
                "severity": "warning",
                "title": f"Attendance risk — {c.get('courseName')}",
                "message": f"{c.get('courseName')} currently has attendance below the satisfactory threshold ({pct:.2f}%).",
            })
    labs = [c for c in subject_performance(dataset) if c.get("courseType") == "L" or c.get("type") == "Laboratory"]
    lab_avg = (sum(c["gradePoint"] or 0 for c in labs) / len(labs)) if labs else 0
    if labs and lab_avg >= 9:
        insights.append({
            "severity": "positive",
            "title": "Practical strength",
            "message": "Your strongest academic performance is visible in programming and laboratory courses.",
        })
    trend = cgpa_trend(dataset)
    completed = [t for t in trend if t.get("completed")]
    if len(completed) >= 2 and completed[-1]["sgpa"] < completed[-2]["sgpa"]:
        insights.append({
            "severity": "warning",
            "title": "Declining semester trend",
            "message": f"Your SGPA decreased from Semester {completed[-2]['semester']} to "
                       f"Semester {completed[-1]['semester']}. Consider reviewing the subjects "
                       "responsible for the decline.",
        })
    if not insights:
        insights.append({
            "severity": "neutral",
            "title": "Keep the momentum",
            "message": "Your records show no immediate concerns. Maintain consistent attendance and coursework.",
        })
    return insights