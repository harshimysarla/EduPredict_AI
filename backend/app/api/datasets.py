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


# ----- Academic records import (approved CSV provider) ---------------------------


async def _read_csv_upload(file: UploadFile) -> pd.DataFrame:
    if not (file.filename or "").endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    content = await file.read()
    try:
        return pd.read_csv(pd.io.common.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read CSV: {str(e)}")


def _save_import_history(db: Session, df: pd.DataFrame, report: dict, current_user: User) -> Dataset:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ds = Dataset(
        name=f"Academic Import ({report['rows']} rows)",
        filename="academic-import.csv",
        uploaded_by=current_user.id,
        status="imported",
        rows=report["rows"],
        columns=len(df.columns),
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


@router.post("/import/validate")
async def validate_import_csv(
    file: UploadFile = File(...),
    column_map: str = Form("{}"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    """Validate an approved academic CSV (preview only, nothing imported)."""
    from app.providers import CsvAcademicDataProvider

    df = await _read_csv_upload(file)
    mapping = json.loads(column_map or "{}")
    provider = CsvAcademicDataProvider(db)
    report = provider.validate_import(df, mapping)
    return report


@router.post("/import")
async def import_csv_records(
    file: UploadFile = File(...),
    column_map: str = Form("{}"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    """Import valid records from an approved academic CSV into the database."""
    from app.providers import CsvAcademicDataProvider

    df = await _read_csv_upload(file)
    mapping = json.loads(column_map or "{}")
    provider = CsvAcademicDataProvider(db)
    try:
        result = provider.import_records(df, mapping)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    _save_import_history(db, df, result, current_user)
    return result


@router.get("/imports/history")
def import_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_faculty_or_admin),
):
    """History of CSV academic imports."""
    rows = (
        db.query(Dataset)
        .filter(Dataset.status == "imported")
        .order_by(Dataset.created_at.desc())
        .all()
    )
    return [
        {
            "id": d.id,
            "name": d.name,
            "rows": d.rows,
            "columns": d.columns,
            "status": d.status,
            "created_at": d.created_at,
            "uploaded_by": d.uploaded_by,
        }
        for d in rows
    ]