import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_faculty_or_admin
from app.models import User, UserRole, Student, Prediction, ModelVersion
from app.schemas import PredictionRequest, PredictionOut
from app.services.base import serialize_prediction
from app.services.ml_service import MLService
from app.ml.pipeline import predict_risk, load_model_package, generate_recommendations, FEATURES

router = APIRouter(prefix="/predictions", tags=["predictions"])
ml_service = MLService()


@router.post("", response_model=dict)
def create_prediction(
    student_id: int,
    features: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    feature_dict = {
        "attendance": features.attendance,
        "previous_performance": features.previous_performance,
        "internal_marks": features.internal_marks,
        "assignment_score": features.assignment_score,
        "engagement": features.engagement,
        "study_hours": features.study_hours or 0,
    }

    try:
        result = ml_service.predict_for_student(db, student, feature_dict)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Prediction failed. Ensure a model is trained.")


@router.get("/students/{student_id}", response_model=list[PredictionOut])
def student_predictions(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if current_user.role == UserRole.STUDENT and student.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    preds = (
        db.query(Prediction)
        .filter(Prediction.student_id == student_id)
        .order_by(Prediction.prediction_date.desc())
        .all()
    )
    return [serialize_prediction(p, student) for p in preds]