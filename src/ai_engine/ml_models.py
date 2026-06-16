from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier

from src.models import AIResult, PartSpec
from src.utils.config import MODEL_ROOT


ANOMALY_MODEL = MODEL_ROOT / "anomaly_isolation_forest.joblib"
MFG_MODEL = MODEL_ROOT / "manufacturability_rf.joblib"


def _feature_vector(part: PartSpec) -> np.ndarray:
    return np.array(
        [
            part.length,
            part.width,
            part.height,
            part.hole_count,
            part.hole_diameter,
            part.tolerance,
        ],
        dtype=float,
    )


def _bootstrap_dataset(seed: int = 42, n: int = 400) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    length = rng.uniform(50, 600, size=n)
    width = rng.uniform(50, 600, size=n)
    height = rng.uniform(4, 50, size=n)
    hole_count = rng.integers(0, 40, size=n)
    hole_d = rng.uniform(2, 30, size=n)
    tol = rng.uniform(0.01, 0.5, size=n)

    x = np.column_stack([length, width, height, hole_count, hole_d, tol])
    risk = (
        (hole_count > 24)
        | (hole_d > np.minimum(length, width) * 0.17)
        | (tol / np.maximum(height, 1e-6) > 0.07)
    ).astype(int)
    return x, risk


def _train_models_if_missing() -> tuple[IsolationForest, RandomForestClassifier]:
    MODEL_ROOT.mkdir(parents=True, exist_ok=True)
    if ANOMALY_MODEL.exists() and MFG_MODEL.exists():
        return joblib.load(ANOMALY_MODEL), joblib.load(MFG_MODEL)

    x, y = _bootstrap_dataset()
    anomaly = IsolationForest(contamination=0.08, random_state=42)
    anomaly.fit(x)

    mfg = RandomForestClassifier(n_estimators=250, random_state=42)
    mfg.fit(x, y)

    joblib.dump(anomaly, ANOMALY_MODEL)
    joblib.dump(mfg, MFG_MODEL)
    return anomaly, mfg


def estimate_cost(part: PartSpec) -> float:
    volume = part.length * part.width * part.height
    complexity = 1.0 + 0.05 * part.hole_count + 0.02 * len(part.features)
    material_factor = {
        "Aluminum": 1.2,
        "Steel": 1.5,
        "StainlessSteel": 1.9,
        "Titanium": 2.6,
    }.get(part.material, 1.4)

    machining_factor = 1.0 + (part.hole_diameter / max(min(part.length, part.width), 1.0))
    return round(0.00004 * volume * complexity * material_factor * machining_factor, 2)


def run_ai_analysis(part: PartSpec) -> AIResult:
    anomaly_model, mfg_model = _train_models_if_missing()
    vector = _feature_vector(part).reshape(1, -1)

    anomaly_score = float(anomaly_model.decision_function(vector)[0])
    anomaly_flag = bool(anomaly_model.predict(vector)[0] == -1)

    risk = int(mfg_model.predict(vector)[0])
    risk_prob = float(mfg_model.predict_proba(vector)[0][1])

    return AIResult(
        anomaly_score=anomaly_score,
        anomaly_flag=anomaly_flag,
        manufacturability_risk=risk,
        manufacturability_probability=risk_prob,
        estimated_cost=estimate_cost(part),
    )
