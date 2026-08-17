import json
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_faculty_or_admin
from app.models import User, ModelVersion
from app.schemas import ModelOut, ModelDetail
from app.services.ml_service import MLService

router = APIRouter(prefix="/models", tags=["models"])
ml_service = MLService()


class TrainRequest(BaseModel):
    dataset_id: int


@router.post("/train", response_model=dict)
def train_model(
    data: TrainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    try:
        result = ml_service.train(data.dataset_id, db, current_user)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("", response_model=list[ModelOut])
def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    return (
        db.query(ModelVersion)
        .order_by(ModelVersion.training_date.desc())
        .all()
    )


@router.get("/{model_id}", response_model=ModelDetail)
def model_detail(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    mv = db.query(ModelVersion).filter(ModelVersion.model_id == model_id).first()
    if not mv:
        raise HTTPException(status_code=404, detail="Model not found")

    feature_importance = []
    confusion_matrix = None
    if mv.metrics:
        try:
            metrics = json.loads(mv.metrics)
        except json.JSONDecodeError:
            metrics = {}
    else:
        metrics = {}

    # Try loading meta for feature importance
    if mv.model_path and os.path.exists(mv.model_path):
        meta_path = mv.model_path.replace("_model.joblib", "_meta.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            importance = meta.get("feature_importance", {})
            feature_importance = [
                {"feature": k, "importance": v} for k, v in importance.items()
            ]
            feature_importance.sort(key=lambda x: x["importance"], reverse=True)
            cm = meta.get("confusion_matrix")
            if cm:
                confusion_matrix = {"matrix": cm}
            else:
                confusion_matrix = {"matrix": [[0, 0], [0, 0]]}

    return ModelDetail(
        id=mv.id,
        model_id=mv.model_id,
        algorithm=mv.algorithm,
        training_date=mv.training_date,
        accuracy=mv.accuracy,
        precision=mv.precision,
        recall=mv.recall,
        f1_score=mv.f1_score,
        roc_auc=mv.roc_auc,
        feature_list=mv.feature_list,
        training_rows=mv.training_rows,
        is_active=mv.is_active,
        metrics=json.dumps(metrics),
        feature_importance=feature_importance,
        confusion_matrix=confusion_matrix,
    )


@router.post("/{model_id}/activate", response_model=ModelOut)
def activate_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    mv = db.query(ModelVersion).filter(ModelVersion.model_id == model_id).first()
    if not mv:
        raise HTTPException(status_code=404, detail="Model not found")

    # Deactivate all, then activate this one
    for m in db.query(ModelVersion).filter(ModelVersion.is_active == True).all():  # noqa: E712
        m.is_active = False
    mv.is_active = True
    db.commit()
    db.refresh(mv)
    return mv