import json
import os
import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_faculty_or_admin
from app.models import User, Dataset
from app.schemas import DatasetOut, DatasetPreview
from app.services.ml_service import MLService

router = APIRouter(prefix="/datasets", tags=["datasets"])
ml_service = MLService()

UPLOAD_DIR = "uploads"


@router.post("/upload", response_model=DatasetOut)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form("student_performance"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dataset = Dataset(
        name=name,
        filename=file.filename or "upload.csv",
        uploaded_by=current_user.id,
        status="uploaded",
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    dest_dir = os.path.join(UPLOAD_DIR, str(dataset.id))
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, dataset.filename)
    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    return dataset


@router.get("", response_model=list[DatasetOut])
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()


@router.get("/{dataset_id}/validate", response_model=DatasetPreview)
def validate_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    path = os.path.join(UPLOAD_DIR, str(dataset.id), dataset.filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Dataset file missing")

    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read CSV: {str(e)}")

    from app.ml.pipeline import validate_dataset as validate_fn

    errors = validate_fn(df)

    preview = df.head(10).to_dict(orient="records")
    return DatasetPreview(
        dataset_id=dataset.id,
        rows=len(df),
        columns=len(df.columns),
        missing_values={str(k): int(v) for k, v in df.isna().sum().items()},
        duplicates=int(df.duplicated().sum()),
        dtypes={str(k): str(v) for k, v in df.dtypes.items()},
        validation_errors=errors,
        preview=preview,
    )