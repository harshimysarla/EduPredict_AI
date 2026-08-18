import json
import os
import re
from datetime import datetime
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler

from app.core.config import settings
from app.ml.dataset_generator import generate_synthetic_dataset

FEATURES = [
    "attendance",
    "previous_performance",
    "internal_marks",
    "assignment_score",
    "engagement",
    "study_hours",
]

RISK_THRESHOLDS = {"low": 0.39, "moderate": 0.69, "high": 1.0}


def risk_level_from_probability(p: float, thresholds: Optional[dict] = None) -> str:
    t = thresholds or RISK_THRESHOLDS
    low = float(t.get("low", RISK_THRESHOLDS["low"]))
    mod = float(t.get("moderate", t.get("high", RISK_THRESHOLDS["moderate"])))
    if p <= low:
        return "low"
    if p <= mod:
        return "moderate"
    return "high"


def validate_dataset(df: pd.DataFrame) -> list:
    errors = []
    required = set(FEATURES)
    if not required.issubset(set(df.columns)):
        missing = required - set(df.columns)
        errors.append(f"Missing required columns: {', '.join(sorted(missing))}")
    if "target" not in df.columns:
        errors.append("Missing required column: target")
    if df.empty:
        errors.append("Dataset is empty")

    numeric_cols = FEATURES + ["target"]
    for col in numeric_cols:
        if col in df.columns:
            non_numeric = pd.to_numeric(df[col], errors="coerce").isna()
            if non_numeric.any():
                errors.append(
                    f"Column '{col}' contains {non_numeric.sum()} non-numeric values"
                )

    if "target" in df.columns:
        targets = df["target"].dropna().unique()
        if not set(targets).issubset({0, 1}):
            errors.append("Column 'target' must contain only 0 or 1 values")
        if len(targets) < 2:
            errors.append("Column 'target' must contain both classes (0 and 1)")
    return errors


def preprocess_data(df: pd.DataFrame, fit_scaler: Optional[StandardScaler] = None):
    df = df.copy()
    df = df[FEATURES + ["target"]].dropna()
    df = df.drop_duplicates()
    X = df[FEATURES]
    y = df["target"].astype(int).values

    if fit_scaler is None:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
    else:
        scaler = fit_scaler
        X_scaled = scaler.transform(X)
    return X_scaled, y, scaler


def train_models(df: pd.DataFrame, seed: int | None = None):
    if seed is None:
        seed = settings.RANDOM_SEED

    X_scaled, y, scaler = preprocess_data(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.25, random_state=seed, stratify=y
    )

    models = {
        "Logistic Regression": LogisticRegression(
            max_iter=1000, random_state=seed, class_weight="balanced"
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=150, max_depth=10, random_state=seed, class_weight="balanced"
        ),
    }

    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        try:
            auc = roc_auc_score(y_test, y_prob)
        except ValueError:
            auc = 0.0

        cm = confusion_matrix(y_test, y_pred).tolist()

        if hasattr(model, "feature_importances_"):
            importance = model.feature_importances_
        elif hasattr(model, "coef_"):
            importance = np.abs(model.coef_[0])
        else:
            importance = np.zeros(len(FEATURES))

        importance_dict = {
            f: round(float(v), 4) for f, v in zip(FEATURES, importance)
        }

        results[name] = {
            "model": model,
            "scaler": scaler,
            "metrics": {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(auc, 4),
            },
            "confusion_matrix": cm,
            "feature_importance": importance_dict,
            "training_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
        }

    return results, scaler, X_train.shape[1]


def select_best_model(results: dict) -> str:
    # Weighted selection: F1 primary, then ROC-AUC, then accuracy
    def score(name):
        m = results[name]["metrics"]
        return m["f1_score"] * 0.5 + m["roc_auc"] * 0.3 + m["accuracy"] * 0.2

    return max(results, key=score)


def save_model_package(results, model_name: str, dataset_id: Optional[int], path: str = None) -> dict:
    if path is None:
        path = settings.MODEL_PATH
    os.makedirs(path, exist_ok=True)

    r = results[model_name]
    model_id = f"{model_name.lower().replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    model_path = os.path.join(path, f"{model_id}_model.joblib")
    preproc_path = os.path.join(path, f"{model_id}_preprocessor.joblib")
    meta_path = os.path.join(path, f"{model_id}_meta.json")

    joblib.dump(r["model"], model_path)
    joblib.dump({"scaler": r["scaler"]}, preproc_path)

    meta = {
        "model_id": model_id,
        "algorithm": model_name,
        "metrics": r["metrics"],
        "confusion_matrix": r["confusion_matrix"],
        "feature_importance": r["feature_importance"],
        "feature_list": FEATURES,
        "training_rows": r["training_rows"],
        "dataset_id": dataset_id,
        "training_date": datetime.utcnow().isoformat(),
        "risk_thresholds": RISK_THRESHOLDS,
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return {"model_id": model_id, "model_path": model_path, "preprocessor_path": preproc_path, **meta}


def load_model_package(model_path: str, preprocessor_path: str, meta_path: str):
    model = joblib.load(model_path)
    preproc = joblib.load(preprocessor_path)
    with open(meta_path) as f:
        meta = json.load(f)
    return model, preproc["scaler"], meta


def predict_risk(model, scaler, meta, features: dict) -> dict:
    """
    features: dict with keys attendance, previous_performance, internal_marks,
              assignment_score, engagement, study_hours
    Returns probability, level, and per-feature contributions.
    """
    X = np.array([[features[f] for f in FEATURES]])
    X_scaled = scaler.transform(X)
    prob = float(model.predict_proba(X_scaled)[0][1])

    # Feature contributions: approximate using permutation-style contribution.
    # For tree models use tree feature importances scaled by feature deviation.
    # For linear models use coefficient * scaled value.
    if hasattr(model, "coef_"):
        coeffs = model.coef_[0]
        contributions = {
            f: round(float(coeffs[i] * X_scaled[0][i]), 4)
            for i, f in enumerate(FEATURES)
        }
    elif hasattr(model, "feature_importances_"):
        contributions = {}
        for i, f in enumerate(FEATURES):
            contributions[f] = round(float(model.feature_importances_[i]) * (X_scaled[0][i]), 4)
    else:
        contributions = {f: 0.0 for f in FEATURES}

    level = risk_level_from_probability(prob, thresholds=meta.get("risk_thresholds"))

    # Normalize contributions to impact levels
    impacts = {}
    max_abs = max([abs(v) for v in contributions.values()] + [0.001])
    for f, v in contributions.items():
        norm = abs(v) / max_abs
        if norm > 0.66:
            impacts[f] = "high"
        elif norm > 0.33:
            impacts[f] = "medium"
        else:
            impacts[f] = "low"

    return {
        "risk_probability": round(prob, 4),
        "risk_level": level,
        "contributions": contributions,
        "impacts": impacts,
        "model_used": meta.get("algorithm", "unknown"),
    }


def compute_student_features(db, student_id: int) -> Optional[dict]:
    """Compute the ML feature vector from a student's actual database records."""
    from sqlalchemy import func
    from app.models import (
        AcademicRecord, AttendanceRecord, EngagementRecord, AssessmentRecord, Student,
    )
    student = db.query(Student).filter(Student.id == student_id).first()
    if student is None:
        return None
    att = db.query(func.avg(AttendanceRecord.attendance_percentage)).filter(
        AttendanceRecord.student_id == student_id).scalar()
    acad = db.query(func.avg(AcademicRecord.total_score)).filter(
        AcademicRecord.student_id == student_id).scalar()
    internal = db.query(func.avg(AssessmentRecord.marks)).filter(
        AssessmentRecord.student_id == student_id).scalar()
    if internal is None:
        internal = db.query(func.avg(AcademicRecord.internal_marks)).filter(
            AcademicRecord.student_id == student_id).scalar()
    assign = db.query(func.avg(AcademicRecord.assignment_score)).filter(
        AcademicRecord.student_id == student_id).scalar()
    eng = db.query(func.avg(EngagementRecord.engagement_score)).filter(
        EngagementRecord.student_id == student_id).scalar()
    if att is None and acad is None and internal is None:
        return None
    return {
        "attendance": float(att or 0),
        "previous_performance": float(acad or 0),
        "internal_marks": float(internal or 0),
        "assignment_score": float(assign or 0),
        "engagement": float(eng or 0),
        "study_hours": 0.0,
    }


def generate_recommendations(features: dict, risk_level: str,
                             thresholds: Optional[dict] = None) -> list:
    recs = []
    if features["attendance"] < 75:
        recs.append("Improve attendance — maintain the 75% attendance target to reduce academic risk.")
    if features["internal_marks"] < 60:
        recs.append("Schedule additional practice for weak assessment areas to raise internal assessment scores.")
    if features["engagement"] < 55:
        recs.append("Encourage classroom participation and mentor interaction to boost engagement.")
    if features["assignment_score"] < 60:
        recs.append("Focus on completing assignments on time and improving assignment quality.")
    if features["previous_performance"] < 55:
        recs.append("Reinforce foundational concepts from previous semesters to build on prior performance.")
    if features["study_hours"] < 3:
        recs.append("Increase daily study hours with a structured study plan.")
    t = thresholds or RISK_THRESHOLDS
    if risk_level == "high":
        recs.append("High risk detected — schedule an academic mentoring session immediately.")
    elif risk_level == "moderate":
        recs.append("Moderate risk detected — schedule a follow-up mentoring session to monitor progress.")
    if not recs:
        recs.append("Maintain current academic habits and continue consistent performance.")
    return recs