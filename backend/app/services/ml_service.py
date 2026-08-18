import json
import os
import pandas as pd
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.ml.pipeline import (
    validate_dataset,
    train_models,
    save_model_package,
    select_best_model,
    load_model_package,
    predict_risk,
    risk_level_from_probability,
    generate_recommendations,
    FEATURES,
)
from app.models import Dataset, ModelVersion, User, Student, Prediction, RiskLevel, Notification
from app.services.base import notify, get_risk_thresholds


class MLService:
    def __init__(self):
        self._active_package = None

    def load_dataset(self, dataset_id: int, db: Session) -> Optional[pd.DataFrame]:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if dataset is None:
            return None
        path = os.path.join("uploads", str(dataset.id), dataset.filename)
        if not os.path.exists(path):
            # fall back to default synthetic dataset
            from app.ml.dataset_generator import generate_synthetic_dataset
            return generate_synthetic_dataset()
        return pd.read_csv(path)

    def process_dataset(self, dataset: Dataset, file_path: str, db: Session) -> dict:
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            dataset.status = "failed"
            dataset.validation_errors = f"Could not read CSV: {str(e)}"
            db.commit()
            return {"ok": False, "errors": [str(e)]}

        errors = validate_dataset(df)
        if errors:
            dataset.status = "failed"
            dataset.validation_errors = "; ".join(errors)
            db.commit()
            return {"ok": False, "errors": errors}

        dataset.rows = len(df)
        dataset.columns = len(df.columns)
        dataset.status = "validated"
        db.commit()

        info = {
            "ok": True,
            "rows": len(df),
            "columns": len(df.columns),
            "missing_values": df.isna().sum().to_dict(),
            "duplicates": int(df.duplicated().sum()),
            "dtypes": {c: str(t) for c, t in df.dtypes.items()},
            "validation_errors": [],
            "preview": df.head(10).to_dict(orient="records"),
        }
        return info

    def train(self, dataset_id: int, db: Session, uploader: User) -> dict:
        df = self.load_dataset(dataset_id, db)
        if df is None:
            raise ValueError("Dataset not found")

        results, scaler, n_features = train_models(df)
        best_name = select_best_model(results)

        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        saved = {}
        winner_mv = None
        for name, r in results.items():
            pkg = save_model_package(results, name, dataset_id)
            mv = ModelVersion(
                model_id=pkg["model_id"],
                algorithm=name,
                dataset_id=dataset_id,
                accuracy=pkg["metrics"]["accuracy"],
                precision=pkg["metrics"]["precision"],
                recall=pkg["metrics"]["recall"],
                f1_score=pkg["metrics"]["f1_score"],
                roc_auc=pkg["metrics"]["roc_auc"],
                feature_list=json.dumps(FEATURES),
                training_rows=pkg["training_rows"],
                is_active=(name == best_name),
                model_path=pkg["model_path"],
                preprocessor_path=pkg["preprocessor_path"],
                metrics=json.dumps(pkg["metrics"]),
            )
            db.add(mv)
            if name == best_name:
                winner_mv = mv
            saved[name] = pkg

        # deactivate all previously active models; only the new winner stays active
        for mv in db.query(ModelVersion).filter(ModelVersion.is_active == True).all():  # noqa: E712
            if mv is not winner_mv:
                mv.is_active = False

        if dataset:
            dataset.status = "trained"
        db.commit()

        notify(
            db, uploader.id,
            "Model training completed",
            f"Training completed. Best model: {best_name} (F1: {results[best_name]['metrics']['f1_score']}).",
            "model_trained",
        )
        db.commit()

        return {
            "best_model": best_name,
            "models": {name: r["metrics"] for name, r in results.items()},
        }

    def predict_for_student(self, db: Session, student: Student, features: dict) -> dict:
        mv = db.query(ModelVersion).filter(ModelVersion.is_active == True).first()  # noqa: E712
        if mv is None or not mv.model_path or not os.path.exists(mv.model_path):
            raise ValueError("No trained model available. Train a model first.")

        model, scaler, meta = load_model_package(
            mv.model_path, mv.preprocessor_path, mv.model_path.replace("_model.joblib", "_meta.json")
        )

        thresholds = get_risk_thresholds(db)
        result = predict_risk(model, scaler, meta, features)
        result["risk_level"] = risk_level_from_probability(
            result["risk_probability"], thresholds=thresholds
        )
        recommendations = generate_recommendations(features, result["risk_level"], thresholds=thresholds)

        prediction = Prediction(
            student_id=student.id,
            risk_probability=result["risk_probability"],
            risk_level=RiskLevel(result["risk_level"]),
            model_name=result["model_used"],
            model_version=mv.model_id,
            feature_contributions=json.dumps(
                {
                    "contributions": result["contributions"],
                    "impacts": result["impacts"],
                }
            ),
        )
        db.add(prediction)
        db.flush()

        # Persist per-feature records (structured prediction_features table)
        from app.models import PredictionFeature
        for f in FEATURES:
            db.add(PredictionFeature(
                prediction_id=prediction.id,
                feature=f,
                value=features.get(f),
                contribution=result["contributions"].get(f),
                impact=result["impacts"].get(f),
            ))

        prediction = Prediction(
            student_id=student.id,
            risk_probability=result["risk_probability"],
            risk_level=RiskLevel(result["risk_level"]),
            model_name=result["model_used"],
            model_version=mv.model_id,
            feature_contributions=json.dumps(
                {
                    "contributions": result["contributions"],
                    "impacts": result["impacts"],
                }
            ),
        )
        db.add(prediction)
        db.flush()

        # Early warning check: compare with previous prediction
        prev = (
            db.query(Prediction)
            .filter(Prediction.student_id == student.id, Prediction.id != prediction.id)
            .order_by(Prediction.prediction_date.desc())
            .first()
        )

        warning = None
        if prev is not None:
            level_order = {"low": 0, "moderate": 1, "high": 2}
            if level_order[result["risk_level"]] > level_order[prev.risk_level.value]:
                warning = {
                    "student_id": student.id,
                    "student_name": student.user.full_name,
                    "student_id_str": student.student_id,
                    "previous_risk": prev.risk_level.value,
                    "current_risk": result["risk_level"],
                    "previous_probability": prev.risk_probability,
                    "current_probability": result["risk_probability"],
                    "change": round(result["risk_probability"] - prev.risk_probability, 4),
                    "contributing_factors": [
                        {"feature": f, "impact": imp}
                        for f, imp in result["impacts"].items()
                        if imp in ("high", "medium")
                    ],
                    "prediction_date": prediction.prediction_date,
                }
                notify(
                    db, student.user_id,
                    "Academic Risk Increased",
                    f"Risk increased from {prev.risk_probability:.0%} to "
                    f"{result['risk_probability']:.0%} (previous: {prev.risk_level.value.upper()} → {result['risk_level'].upper()}).",
                    "risk_increased",
                    student.id,
                )
        elif result["risk_level"] == "high":
            notify(
                db, student.user_id,
                "High risk detected",
                f"{student.user.full_name} is classified as high risk ({result['risk_probability']:.1%} probability).",
                "high_risk",
                student.id,
            )

        db.commit()

        return {
            "prediction": {
                "id": prediction.id,
                "student_id": student.student_id,
                "student_name": student.user.full_name,
                "risk_probability": result["risk_probability"],
                "risk_level": result["risk_level"],
                "model": result["model_used"],
                "prediction_date": prediction.prediction_date,
                "factors": [
                    {"feature": f, "impact": imp}
                    for f, imp in result["impacts"].items()
                ],
                "recommendations": recommendations,
            },
            "warning": warning,
        }