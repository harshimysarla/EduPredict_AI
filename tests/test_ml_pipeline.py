import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

import pytest
import pandas as pd

from app.ml.dataset_generator import generate_synthetic_dataset, compute_risk_probability
from app.ml.pipeline import (
    validate_dataset,
    preprocess_data,
    train_models,
    select_best_model,
    load_model_package,
    risk_level_from_probability,
    predict_risk,
    generate_recommendations,
    FEATURES,
)


@pytest.fixture(scope="module")
def synthetic_df():
    return generate_synthetic_dataset(200, seed=7)


def test_dataset_is_reproducible():
    a = generate_synthetic_dataset(100, seed=1)
    b = generate_synthetic_dataset(100, seed=1)
    pd.testing.assert_frame_equal(a, b)
    c = generate_synthetic_dataset(100, seed=2)
    assert not a.equals(c)


def test_dataset_has_all_features(synthetic_df):
    assert set(FEATURES + ["target"]) <= set(synthetic_df.columns)
    for f in FEATURES:
        assert 0 <= synthetic_df[f].min() <= 100


def test_target_is_binary_and_balanced(synthetic_df):
    counts = synthetic_df["target"].value_counts()
    assert set(counts.index) <= {0, 1}
    assert counts.min() > int(0.15 * len(synthetic_df))


def test_validation_accepts_good_dataset(synthetic_df):
    assert validate_dataset(synthetic_df) == []


def test_validation_rejects_missing_column(synthetic_df):
    bad = synthetic_df.drop(columns=["attendance"])
    assert any("attendance" in e for e in validate_dataset(bad))


def test_validation_rejects_non_numeric(synthetic_df):
    bad = synthetic_df.copy()
    bad["attendance"] = bad["attendance"].astype(object)
    bad.loc[0, "attendance"] = "abc"
    assert validate_dataset(bad)


def test_validation_rejects_single_class(synthetic_df):
    bad = synthetic_df.copy()
    bad["target"] = 1
    assert validate_dataset(bad)


def test_preprocessing_drops_missing_and_duplicates():
    df = generate_synthetic_dataset(50)
    df.loc[0, "attendance"] = None
    df = pd.concat([df, df.iloc[[1]]], ignore_index=True)
    X, y, scaler = preprocess_data(df)
    assert X.shape[0] == len(df.dropna().drop_duplicates())


def test_train_models_produce_both_models(synthetic_df):
    results, scaler, n = train_models(synthetic_df, seed=42)
    assert set(results.keys()) == {"Random Forest", "Logistic Regression"}
    for name, r in results.items():
        m = r["metrics"]
        assert 0 <= m["accuracy"] <= 1
        assert 0 <= m["f1_score"] <= 1
        assert r["confusion_matrix"]
        assert len(r["feature_importance"]) == len(FEATURES)
    assert n == len(FEATURES)


def test_models_learn_pattern(synthetic_df):
    # High risk student
    high = {
        "attendance": 30, "previous_performance": 35, "internal_marks": 30,
        "assignment_score": 35, "engagement": 25, "study_hours": 1,
    }
    # Low risk student
    low = {
        "attendance": 92, "previous_performance": 88, "internal_marks": 90,
        "assignment_score": 85, "engagement": 88, "study_hours": 7,
    }
    results, scaler, _ = train_models(synthetic_df, seed=42)
    for name, r in results.items():
        model = r["model"]
        p_high = model.predict_proba(scaler.transform([[high[f] for f in FEATURES]]))[0][1]
        p_low = model.predict_proba(scaler.transform([[low[f] for f in FEATURES]]))[0][1]
        assert p_high > 0.6, f"{name}: high-risk probability too low ({p_high:.2f})"
        assert p_low < 0.4, f"{name}: low-risk probability too high ({p_low:.2f})"


def test_select_best_model_returns_valid_name(synthetic_df):
    results, _, _ = train_models(synthetic_df)
    assert select_best_model(results) in ("Random Forest", "Logistic Regression")


def test_risk_level_thresholds():
    assert risk_level_from_probability(0.1) == "low"
    assert risk_level_from_probability(0.5) == "moderate"
    assert risk_level_from_probability(0.8) == "high"


def test_predict_risk_returns_contributions(synthetic_df):
    results, _, _ = train_models(synthetic_df, seed=42)
    model = results["Random Forest"]["model"]
    meta = {"algorithm": "Random Forest"}
    features = {"attendance": 60, "previous_performance": 55, "internal_marks": 50, "assignment_score": 55, "engagement": 45, "study_hours": 3}
    out = predict_risk(model, results["Random Forest"]["scaler"], meta, features)
    assert 0 <= out["risk_probability"] <= 1
    assert out["risk_level"] in ("low", "moderate", "high")
    assert set(out["impacts"].keys()) == set(FEATURES)
    assert set(out["impacts"].values()) <= {"high", "medium", "low"}
    assert set(out["contributions"].keys()) == set(FEATURES)


def test_recommendations_are_data_driven():
    low = {"attendance": 90, "previous_performance": 85, "internal_marks": 88, "assignment_score": 82, "engagement": 80, "study_hours": 6}
    low_recs = generate_recommendations(low, "low")
    assert not any("Improve attendance" in r for r in low_recs)

    high = {"attendance": 40, "previous_performance": 45, "internal_marks": 40, "assignment_score": 42, "engagement": 30, "study_hours": 1}
    high_recs = generate_recommendations(high, "high")
    assert any("mentoring session immediately" in r for r in high_recs)
    assert any("Improve attendance" in r for r in high_recs)
    assert any("study" in r.lower() for r in high_recs)


def test_compute_risk_probability_monotonic():
    rng_hi = __import__("numpy").random.default_rng(5)
    rng_lo = __import__("numpy").random.default_rng(5)
    base = {"attendance": 70, "previous_performance": 70, "internal_marks": 70, "assignment_score": 70, "engagement": 70, "study_hours": 4}
    p_hi = compute_risk_probability({**base, "attendance": 95}, rng_hi)
    p_lo = compute_risk_probability({**base, "attendance": 40}, rng_lo)
    assert p_lo > p_hi


def test_model_save_and_load_roundtrip(tmp_path):
    from app.ml.pipeline import save_model_package
    df = generate_synthetic_dataset(80, seed=3)
    results, _, _ = train_models(df, seed=3)
    pkg = save_model_package(results, "Random Forest", None, path=str(tmp_path))
    model, scaler, meta = load_model_package(pkg["model_path"], pkg["preprocessor_path"], pkg["model_path"].replace("_model.joblib", "_meta.json"))
    assert meta["algorithm"] == "Random Forest"
    assert len(meta["feature_list"]) == 6
    probs = model.predict_proba(scaler.transform([[50] * 6]))
    assert probs.shape == (1, 2)