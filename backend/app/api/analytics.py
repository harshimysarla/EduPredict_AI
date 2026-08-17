from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_faculty_or_admin
from app.models import (
    User, Student, AcademicRecord, AttendanceRecord, EngagementRecord,
    Prediction, RiskLevel, Section, Department, Subject, Intervention, InterventionStatus,
)
from app.services.base import get_student_summary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
def dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    students = db.query(Student).filter(Student.is_active == True).all()  # noqa: E712

    total = len(students)
    summaries = [get_student_summary(db, s) for s in students]

    def avg(key):
        vals = [x[key] for x in summaries if x.get(key) is not None]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    risk_counts = {"low": 0, "moderate": 0, "high": 0, "unpredicted": 0}
    for x in summaries:
        if x["risk_level"] is None:
            risk_counts["unpredicted"] += 1
        else:
            risk_counts[x["risk_level"]] += 1

    # Attendance vs performance scatter
    scatter = []
    for s, x in zip(students, summaries):
        if x["attendance"] is not None and x["average_score"] is not None:
            scatter.append(
                {
                    "student": s.user.full_name,
                    "student_id": s.student_id,
                    "attendance": x["attendance"],
                    "score": x["average_score"],
                }
            )

    # Performance trend: average total score per semester
    trend = (
        db.query(AcademicRecord.semester, func.avg(AcademicRecord.total_score))
        .group_by(AcademicRecord.semester)
        .order_by(AcademicRecord.semester)
        .all()
    )
    performance_trend = [{"semester": sem, "average": round(avg_, 2)} for sem, avg_ in trend]

    # Subject performance
    subject_perf = (
        db.query(
            Subject.name,
            func.avg(AcademicRecord.total_score),
            func.count(AcademicRecord.id),
        )
        .join(AcademicRecord, AcademicRecord.subject_id == Subject.id)
        .group_by(Subject.name)
        .all()
    )
    subject_performance = [
        {"subject": name, "average": round(a, 2), "records": c} for name, a, c in subject_perf
    ]

    # Attendance vs performance correlation
    att_scores = [(x["attendance"], x["average_score"]) for x in summaries if x["attendance"] and x["average_score"]]
    corr_att_perf = _pearson(att_scores)

    eng_scores = [(x["engagement"], x["average_score"]) for x in summaries if x["engagement"] and x["average_score"]]
    corr_eng_perf = _pearson(eng_scores)

    # Students requiring attention: high risk sorted by probability
    attention = []
    for s, x in zip(students, summaries):
        if x["risk_level"] == "high":
            attention.append(
                {
                    "id": s.id,
                    "student_id": s.student_id,
                    "name": s.user.full_name,
                    "attendance": x["attendance"],
                    "average_score": x["average_score"],
                    "engagement": x["engagement"],
                    "risk_probability": x["risk_probability"],
                    "risk_level": x["risk_level"],
                }
            )
    attention.sort(key=lambda a: a["risk_probability"] or 0, reverse=True)

    avg_attendance = avg("attendance")
    below_threshold = sum(1 for x in summaries if x["attendance"] is not None and x["attendance"] < 75)

    return {
        "kpis": {
            "total_students": total,
            "high_risk": risk_counts["high"],
            "moderate_risk": risk_counts["moderate"],
            "low_risk": risk_counts["low"],
            "unpredicted": risk_counts["unpredicted"],
            "average_performance": avg("average_score"),
            "average_attendance": avg_attendance,
            "average_engagement": avg("engagement"),
            "below_attendance_threshold": below_threshold,
        },
        "risk_distribution": [
            {"name": "Low Risk", "value": risk_counts["low"], "level": "low"},
            {"name": "Moderate Risk", "value": risk_counts["moderate"], "level": "moderate"},
            {"name": "High Risk", "value": risk_counts["high"], "level": "high"},
        ],
        "performance_trend": performance_trend,
        "attendance_performance_scatter": scatter,
        "subject_performance": subject_performance,
        "students_requiring_attention": attention,
        "correlations": {
            "attendance_performance": round(corr_att_perf, 3),
            "engagement_performance": round(corr_eng_perf, 3),
        },
        "engagement_distribution": _engagement_distribution(summaries),
        "score_distribution": _score_distribution(students, db),
    }


def _pearson(pairs):
    n = len(pairs)
    if n < 2:
        return 0.0
    x_mean = sum(p[0] for p in pairs) / n
    y_mean = sum(p[1] for p in pairs) / n
    num = sum((p[0] - x_mean) * (p[1] - y_mean) for p in pairs)
    den = (sum((p[0] - x_mean) ** 2 for p in pairs) * sum((p[1] - y_mean) ** 2 for p in pairs)) ** 0.5
    return num / den if den else 0.0


def _engagement_distribution(summaries):
    buckets = {"low": 0, "medium": 0, "high": 0}
    for x in summaries:
        e = x["engagement"]
        if e is None:
            continue
        if e < 45:
            buckets["low"] += 1
        elif e < 70:
            buckets["medium"] += 1
        else:
            buckets["high"] += 1
    return [
        {"name": "Low Engagement", "value": buckets["low"]},
        {"name": "Medium Engagement", "value": buckets["medium"]},
        {"name": "High Engagement", "value": buckets["high"]},
    ]


def _score_distribution(students, db):
    buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for s in students:
        avg_score = (
            db.query(func.avg(AcademicRecord.total_score))
            .filter(AcademicRecord.student_id == s.id)
            .scalar()
        )
        if avg_score is None:
            continue
        if avg_score <= 20:
            buckets["0-20"] += 1
        elif avg_score <= 40:
            buckets["21-40"] += 1
        elif avg_score <= 60:
            buckets["41-60"] += 1
        elif avg_score <= 80:
            buckets["61-80"] += 1
        else:
            buckets["81-100"] += 1
    return [{"range": k, "count": v} for k, v in buckets.items()]


@router.get("/intervention-impact")
def intervention_impact(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return None

    interventions = (
        db.query(Intervention)
        .filter(Intervention.student_id == student_id)
        .order_by(Intervention.assigned_date.asc())
        .all()
    )
    if not interventions:
        return {
            "student_id": student_id,
            "student_name": student.user.full_name,
            "intervention_count": 0,
            "completed_count": 0,
            "message": "No interventions found for this student.",
        }

    first_date = interventions[0].assigned_date

    def snapshot_before():
        pred = (
            db.query(Prediction)
            .filter(
                Prediction.student_id == student_id,
                Prediction.prediction_date <= first_date,
            )
            .order_by(Prediction.prediction_date.desc())
            .first()
        )
        perf = (
            db.query(func.avg(AcademicRecord.total_score))
            .join(AcademicRecord, AcademicRecord.id == AcademicRecord.id)
            .filter(AcademicRecord.student_id == student_id)
            .scalar()
        )
        return pred, perf

    completed = [i for i in interventions if i.status == InterventionStatus.COMPLETED]
    completed_date = completed[-1].completed_date if completed else None

    # Latest prediction overall (after = latest)
    latest = (
        db.query(Prediction)
        .filter(Prediction.student_id == student_id)
        .order_by(Prediction.prediction_date.desc())
        .first()
    )

    # Current performance = average of semester 2+ records (after first intervention semester)
    current_sem = student.current_semester
    perf_before = (
        db.query(func.avg(AcademicRecord.total_score))
        .filter(
            AcademicRecord.student_id == student_id,
            AcademicRecord.semester == 1,
        )
        .scalar()
    )
    perf_after = (
        db.query(func.avg(AcademicRecord.total_score))
        .filter(
            AcademicRecord.student_id == student_id,
            AcademicRecord.semester == student.current_semester,
        )
        .scalar()
    )
    if perf_after is None:
        perf_after = (
            db.query(func.avg(AcademicRecord.total_score))
            .filter(AcademicRecord.student_id == student_id)
            .scalar()
        )

    att_before = (
        db.query(func.avg(AttendanceRecord.attendance_percentage))
        .filter(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.semester == 1,
        )
        .scalar()
    )
    att_after = (
        db.query(func.avg(AttendanceRecord.attendance_percentage))
        .filter(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.semester == student.current_semester,
        )
        .scalar()
    )
    if att_after is None:
        att_after = (
            db.query(func.avg(AttendanceRecord.attendance_percentage))
            .filter(AttendanceRecord.student_id == student_id)
            .scalar()
        )

    # Risk before: first prediction, risk after: latest prediction
    first_pred = (
        db.query(Prediction)
        .filter(Prediction.student_id == student_id)
        .order_by(Prediction.prediction_date.asc())
        .first()
    )

    return {
        "student_id": student_id,
        "student_name": student.user.full_name,
        "risk_before": round(first_pred.risk_probability, 2) if first_pred else None,
        "risk_after": round(latest.risk_probability, 2) if latest else None,
        "performance_before": round(perf_before, 2) if perf_before else None,
        "performance_after": round(perf_after, 2) if perf_after else None,
        "attendance_before": round(att_before, 2) if att_before else None,
        "attendance_after": round(att_after, 2) if att_after else None,
        "risk_reduction": (
            round(first_pred.risk_probability - latest.risk_probability, 2)
            if first_pred and latest else None
        ),
        "performance_improvement": (
            round(perf_after - perf_before, 2) if perf_after and perf_before else None
        ),
        "attendance_improvement": (
            round(att_after - att_before, 2) if att_after and att_before else None
        ),
        "intervention_count": len(interventions),
        "completed_count": len(completed),
    }