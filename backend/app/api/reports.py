import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_faculty_or_admin, get_current_user
from app.models import (
    User, UserRole, Student, AcademicRecord, AttendanceRecord, EngagementRecord,
    Prediction, Intervention, Subject, FacultyProfile,
)
from app.services.base import get_student_summary, faculty_scope_filter
from app.ml.pipeline import load_model_package, predict_risk, generate_recommendations, FEATURES

router = APIRouter(prefix="/reports", tags=["reports"])


def _check_scope(db: Session, student: Student, current_user: User) -> None:
    if current_user.role == UserRole.ADMIN:
        return
    fp = db.query(FacultyProfile).filter(FacultyProfile.user_id == current_user.id).first()
    if fp is None or student.section is None or \
            student.section.department_id not in faculty_scope_filter(fp):
        raise HTTPException(status_code=403, detail="Access denied to this student")


def _assemble_report(db: Session, student: Student) -> dict:
    summary = get_student_summary(db, student)
    section_name = student.section.name if student.section else ""
    dept_name = student.section.department.name if student.section else ""

    academics = (
        db.query(AcademicRecord)
        .filter(AcademicRecord.student_id == student.id)
        .order_by(AcademicRecord.semester)
        .all()
    )
    attendance = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student.id)
        .order_by(AttendanceRecord.semester, AttendanceRecord.month)
        .all()
    )
    predictions = (
        db.query(Prediction)
        .filter(Prediction.student_id == student.id)
        .order_by(Prediction.prediction_date.desc())
        .limit(5)
        .all()
    )
    interventions = (
        db.query(Intervention)
        .filter(Intervention.student_id == student.id)
        .order_by(Intervention.assigned_date.desc())
        .all()
    )

    latest_pred = predictions[0] if predictions else None
    factors = []
    recommendations = []
    if latest_pred and latest_pred.feature_contributions:
        import json

        try:
            contrib = json.loads(latest_pred.feature_contributions)
            factors = [
                {"feature": f, "impact": contrib.get("impacts", {}).get(f, "medium")}
                for f in contrib.get("contributions", {})
            ]
        except Exception:
            pass

    # Regenerate recommendations from current data if possible
    avg_att = summary.get("attendance")
    avg_score = summary.get("average_score")
    avg_eng = summary.get("engagement")
    if avg_att is not None and avg_score is not None:
        recommendations = generate_recommendations(
            {
                "attendance": avg_att or 0,
                "previous_performance": avg_score or 0,
                "internal_marks": avg_score or 0,
                "assignment_score": avg_score or 0,
                "engagement": avg_eng or 0,
                "study_hours": 0,
            },
            latest_pred.risk_level.value if latest_pred else "low",
        )

    return {
        "student": {
            "name": student.user.full_name,
            "student_id": student.student_id,
            "email": student.user.email,
            "department": dept_name,
            "section": section_name,
            "admission_year": student.admission_year,
            "current_semester": student.current_semester,
        },
        "academic_health": summary,
        "academics": [
            {
                "subject": subject.name if (subject := db.query(Subject).filter(Subject.id == r.subject_id).first()) else str(r.subject_id),
                "semester": r.semester,
                "internal_marks": r.internal_marks,
                "assignment_score": r.assignment_score,
                "exam_score": r.exam_score,
                "total_score": r.total_score,
                "grade": r.grade,
            }
            for r in academics
        ],
        "attendance": [
            {
                "semester": a.semester,
                "month": a.month,
                "classes_held": a.classes_held,
                "classes_attended": a.classes_attended,
                "percentage": a.attendance_percentage,
            }
            for a in attendance
        ],
        "predictions": [
            {
                "date": p.prediction_date,
                "probability": p.risk_probability,
                "level": p.risk_level.value,
                "model": p.model_name,
            }
            for p in predictions
        ],
        "prediction_summary": {
            "probability": latest_pred.risk_probability if latest_pred else None,
            "level": latest_pred.risk_level.value if latest_pred else None,
            "date": latest_pred.prediction_date if latest_pred else None,
            "model": latest_pred.model_name if latest_pred else None,
        },
        "risk_factors": factors,
        "recommendations": recommendations,
        "interventions": [
            {
                "type": i.type.value,
                "title": i.title,
                "status": i.status.value,
                "assigned_date": i.assigned_date,
                "follow_up_date": i.follow_up_date,
                "notes": i.notes,
            }
            for i in interventions
        ],
        "generated_at": datetime.utcnow(),
    }


@router.get("/student/{student_id}")
def student_report(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    _check_scope(db, student, current_user)
    report = _assemble_report(db, student)
    report["generated_at"] = datetime.utcnow()
    return report


@router.get("/student/{student_id}/csv")
def student_report_csv(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    _check_scope(db, student, current_user)
    report = _assemble_report(db, student)

    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["Field", "Value"])
    s = report["student"]
    for k, v in s.items():
        writer.writerow([k.replace("_", " ").title(), v])
    writer.writerow([])

    health = report["academic_health"]
    writer.writerow(["ACADEMIC HEALTH"])
    for k, v in health.items():
        writer.writerow([k.replace("_", " ").title(), v])
    writer.writerow([])

    writer.writerow(["PREDICTIONS"])
    writer.writerow(["Date", "Probability", "Level", "Model"])
    for p in report["predictions"]:
        writer.writerow([p["date"], p["probability"], p["level"], p["model"]])
    writer.writerow([])

    writer.writerow(["ACADEMIC RECORDS"])
    writer.writerow(["Subject", "Semester", "Internal", "Assignment", "Exam", "Total", "Grade"])
    for a in report["academics"]:
        writer.writerow([a["subject"], a["semester"], a["internal_marks"], a["assignment_score"], a["exam_score"], a["total_score"], a["grade"]])
    writer.writerow([])

    writer.writerow(["RECOMMENDATIONS"])
    for r in report["recommendations"]:
        writer.writerow([r])
    writer.writerow([])

    writer.writerow(["INTERVENTIONS"])
    writer.writerow(["Type", "Title", "Status", "Assigned", "Follow-up", "Notes"])
    for i in report["interventions"]:
        writer.writerow([i["type"], i["title"], i["status"], i["assigned_date"], i["follow_up_date"], i["notes"]])

    buf.seek(0)
    filename = f"report_{student.student_id}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
