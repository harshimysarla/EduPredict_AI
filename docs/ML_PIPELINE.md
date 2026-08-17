# ML Pipeline & Synthetic Data

## Feature Set

Six numeric features (bounded to plausible academic ranges):

| Feature | Meaning | μ | σ |
|---|---|---|---|
| `attendance` | attendance percentage | 78 | 14 |
| `previous_performance` | GPA scaled to 0–100 | 65 | 16 |
| `internal_marks` | current internal assessment (0–100) | 62 | 17 |
| `assignment_score` | assignment average (0–100) | 68 | 15 |
| `engagement` | LMS participation / engagement score | 60 | 18 |
| `study_hours` | hours studied per week | 4.5 | 2.0 |

## Synthetic Data Generation

`backend/app/ml/dataset_generator.py` — reproducible (`seed=42`), used both for the shipped dataset (`data/student_performance.csv`, 600 rows) and the seed script.

1. **Sample features** from normal distributions (clipped to valid ranges), with light correlation (internal marks influenced by attendance) so models can learn real structure.
2. **Standardize** each feature and compute a weighted performance composite:

```
z_i      = (x_i − μ_i) / σ_i
perf     = 0.35·z_attendance + 0.30·z_internal + 0.15·z_previous
           + 0.15·z_engagement + 0.05·z_assignment + 0.00·z_study
```

3. **Risk probability** (logistic with negative sign — low features push risk up):

```
p = sigmoid(−2.25 · perf − 0.7 + noise),   noise ~ N(0, 0.1)
```

4. **Target**: `target = 1` (at risk) if `p > 0.5`, else 0.

The seed script uses the same `compute_risk_probability()` so seeded students are consistent with the dataset. Resulting split: ~33% at-risk, ~67% safe.

> **Note on calibration** — thresholds and weights are heuristic, not empirical. In production, calibrate the logit intercept/shift on real historical data so the risk distribution matches observed outcome rates.

## Preprocessing

- Column checks (all features present, numeric, non-null, finite)
- Rows outside plausible bounds are dropped; `target` coerced to int
- Features standardized with `StandardScaler` (fitted on training split)
- 80/20 stratified train/test split (seed from settings)

## Models

| Model | Purpose |
|---|---|
| Logistic Regression | Interpretable baseline (linear decision surface) |
| Random Forest | Non-linear ensemble capturing feature interactions |

Both are trained on the same split and scored on the held-out test set.

## Model Selection

```
score = 0.5 · F1 + 0.3 · ROC-AUC + 0.2 · Accuracy
```

The higher-scoring model is marked active for the new training run.

## Persistence

Artifacts written to `models/` (root, configurable via `MODEL_PATH`):

- `<algorithm>_<timestamp>_model.joblib` — estimator
- `<algorithm>_<timestamp>_preprocessor.joblib` — fitted scaler
- `<algorithm>_<timestamp>_meta.json` — metrics, feature list, training rows, timestamp

Each trained artifact is registered as a `ModelVersion` row (with `is_active` flag); training **deactivates all previous versions** so exactly one production model exists. Admins can also promote any version via `POST /models/{id}/activate`.

## Prediction & Explanation

`predict_risk(model, scaler, meta, features)`:

- scale features with the fitted scaler, predict risk probability
- per-factor contributions:
  - linear model: `coef_i · scaled_value_i`
  - tree ensemble: `importance_i · scaled_value_i`
- contributions are normalized to explain the deviation of the logit from its mean; absolute values rank the driving factors

## Risk Levels

| Risk probability | Level |
|---|---|
| ≤ 0.39 | low |
| ≤ 0.69 | moderate |
| > 0.69 | high |

## Recommendations

Rule-based recommendations (in `generate_recommendations`) fire from the predicted factors, e.g.:

- attendance < 75 → attendance improvement plan
- internal marks < 60 → remedial classes / tutor session
- engagement < 50 → participation program
- previous performance < 50 → bridge course
- overall risk high → immediate academic counselling + follow-up

## Early-Warning Flow

`MLService.predict_for_student` compares the new prediction with the student's previous one. If the risk level escalates (e.g. low → high), a `Notification` is created for faculty/advisors (dashboard bell) and the event is visible on the student's prediction timeline.

## Tests

- `tests/test_ml_pipeline.py` — 16 unit tests: generation statistics, monotonic risk behavior, validation, preprocessing, training reproducibility, metric shapes, selection, save/load roundtrip, explanation, recommendations, risk thresholds.
- `tests/test_api.py` — end-to-end API tests including dataset upload → validation → training → versioning → prediction.
