import pandas as pd
import numpy as np
from app.core.config import settings

# ---------------------------------------------------------------------------
# Synthetic target generation rule (DOCUMENTED for demonstration purposes)
#
# The dataset is SYNTHETIC. It does NOT represent real students.
#
# Risk of poor performance is driven by:
#   attendance, internal marks, previous performance, engagement, assignment
#   scores, and study hours.
#
# Generation procedure:
#   1. Draw realistic feature values from normal distributions (clipped to
#      plausible academic ranges) with correlated structure so the ML models
#      can learn meaningful patterns.
#   2. Standardize each feature (z-score) and compute a weighted performance
#      composite:
#        z_i = (x_i - mu_i) / sigma_i
#        perf_score = sum(w_i * z_i), w = (0.35 attendance, 0.30 internal,
#                         0.15 previous_performance, 0.15 engagement,
#                         0.05 assignment_score)
#   3. Convert to a risk probability via the logistic function — low values of
#      the features push risk up (inverted sign):
#        p = sigmoid(-2.25 * perf_score - 0.7 + noise)
#   4. target = 1 (at risk) if p > 0.5
#
# The weighting follows the pedagogical intuition that current attendance and
# internal assessment are the strongest early indicators of academic risk.
# A random seed is used so generation is reproducible.
# ---------------------------------------------------------------------------


def compute_risk_probability(features: dict, rng: np.random.Generator = None) -> float:
    """Compute the documented synthetic risk probability for a feature dict."""
    cols = ["attendance", "previous_performance", "internal_marks",
            "assignment_score", "engagement", "study_hours"]
    sample = np.array([[features.get(c, 0) for c in cols]])
    mu = np.array([78, 65, 62, 68, 60, 4.5])
    sigma = np.array([14, 16, 17, 15, 18, 2.0])
    z = ((sample - mu) / sigma)[0]
    weights = np.array([0.35, 0.15, 0.30, 0.05, 0.15, 0.0])
    perf_score = float(z @ weights)
    noise = rng.normal(0, 0.1) if rng is not None else 0.0
    return float(1 / (1 + np.exp(-(-2.25 * perf_score - 0.7 + noise))))


def generate_synthetic_dataset(n_rows: int = 600, seed: int | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed if seed is not None else settings.RANDOM_SEED)

    attendance = np.clip(rng.normal(78, 14, n_rows), 20, 100).round(2)
    previous_performance = np.clip(rng.normal(65, 16, n_rows), 20, 100).round(2)
    internal_marks = np.clip(rng.normal(62, 17, n_rows), 15, 100).round(2)
    assignment_score = np.clip(rng.normal(68, 15, n_rows), 20, 100).round(2)
    engagement = np.clip(rng.normal(60, 18, n_rows), 10, 100).round(2)
    study_hours = np.clip(rng.normal(4.5, 2.0, n_rows), 0.5, 14).round(1)

    # correlated structure so the model can learn real patterns
    internal_marks = internal_marks + 0.35 * (attendance - attendance.mean())
    assignment_score = assignment_score + 0.3 * (engagement - engagement.mean())
    internal_marks = np.clip(internal_marks, 15, 100).round(2)
    assignment_score = np.clip(assignment_score, 20, 100).round(2)

    probs = np.array([
        compute_risk_probability(
            {
                "attendance": a, "previous_performance": p,
                "internal_marks": im, "assignment_score": as_,
                "engagement": e, "study_hours": sh,
            },
            rng,
        )
        for a, p, im, as_, e, sh in zip(
            attendance, previous_performance, internal_marks,
            assignment_score, engagement, study_hours,
        )
    ])
    target = (probs > 0.5).astype(int)

    df = pd.DataFrame(
        {
            "student_id": [f"SYN{1000 + i}" for i in range(n_rows)],
            "attendance": attendance,
            "previous_performance": previous_performance,
            "internal_marks": internal_marks,
            "assignment_score": assignment_score,
            "engagement": engagement,
            "study_hours": study_hours,
            "target": target,
        }
    )
    return df


def generate_student_performance_csv(path: str, n_rows: int = 600) -> None:
    df = generate_synthetic_dataset(n_rows)
    df.to_csv(path, index=False)


if __name__ == "__main__":
    import os

    os.makedirs("data", exist_ok=True)
    generate_student_performance_csv("data/student_performance.csv")
    print("Generated data/student_performance.csv")
