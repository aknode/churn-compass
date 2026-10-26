"""Leakage-safe Telco churn training and batch scoring."""

from pathlib import Path
import hashlib, json, platform
import numpy as np
import pandas as pd
import joblib, sklearn
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    fbeta_score,
    confusion_matrix,
    brier_score_loss,
    precision_recall_curve,
)

BASE = Path(__file__).resolve().parents[1]
NUM = ["tenure", "MonthlyCharges", "TotalCharges"]
CAT = [
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
]
FEATURES = NUM + CAT
OPTIONS = {
    "PhoneService": ["Yes", "No"],
    "MultipleLines": ["Yes", "No", "No phone service"],
    "InternetService": ["DSL", "Fiber optic", "No"],
    **{
        k: ["Yes", "No", "No internet service"]
        for k in [
            "OnlineSecurity",
            "OnlineBackup",
            "DeviceProtection",
            "TechSupport",
            "StreamingTV",
            "StreamingMovies",
        ]
    },
    "Contract": ["Month-to-month", "One year", "Two year"],
    "PaperlessBilling": ["Yes", "No"],
    "PaymentMethod": [
        "Electronic check",
        "Mailed check",
        "Bank transfer (automatic)",
        "Credit card (automatic)",
    ],
}


def validate(frame):
    if frame.empty:
        raise ValueError("Provide at least one customer.")
    if len(frame) > 10000:
        raise ValueError("Maximum 10,000 customers per request.")
    missing = set(FEATURES) - set(frame.columns)
    if missing:
        raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
    x = frame[FEATURES].copy()
    for col in NUM:
        raw = x[col]
        x[col] = pd.to_numeric(raw, errors="coerce")
        allowed_blank = raw.isna() | raw.astype(str).str.strip().eq("")
        if (x[col].isna() & ~allowed_blank).any():
            raise ValueError(f"{col} must be numeric.")
        if col != "TotalCharges" and x[col].isna().any():
            raise ValueError(f"{col} is required.")
        if ((x[col].dropna() < 0) | ~np.isfinite(x[col].dropna())).any():
            raise ValueError(f"{col} must be finite and nonnegative.")
    if (x.tenure > 1200).any():
        raise ValueError("tenure must be in months, at most 1200.")
    for col, choices in OPTIONS.items():
        if not x[col].isin(choices).all():
            raise ValueError(f"Invalid {col}; allowed: {choices}")
    return x


def preprocess():
    return ColumnTransformer(
        [
            (
                "num",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                NUM,
            ),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
        ]
    )


def metrics(y, p, t):
    pred = p >= t
    return {
        "roc_auc": float(roc_auc_score(y, p)),
        "average_precision": float(average_precision_score(y, p)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f2": float(fbeta_score(y, pred, beta=2, zero_division=0)),
        "brier_score": float(brier_score_loss(y, p)),
        "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
    }


def train(csv_path, output=None):
    out = Path(output or BASE / "artifacts")
    out.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(csv_path)
    x = validate(raw)
    y = raw.Churn.map({"Yes": 1, "No": 0})
    if y.isna().any() or raw.customerID.duplicated().any():
        raise ValueError("Invalid target or duplicate customer IDs.")
    train_i, rest_i = train_test_split(
        np.arange(len(x)), test_size=0.4, stratify=y, random_state=42
    )
    val_i, test_i = train_test_split(
        rest_i, test_size=0.5, stratify=y.iloc[rest_i], random_state=42
    )
    models = {
        "prior_baseline": DummyClassifier(strategy="prior"),
        "logistic_regression": LogisticRegression(C=1, max_iter=2000, random_state=42),
        "random_forest": RandomForestClassifier(
            n_estimators=160,
            min_samples_leaf=8,
            max_depth=12,
            random_state=42,
            n_jobs=2,
        ),
    }
    fitted = {}
    validation = {}
    for name, est in models.items():
        model = Pipeline([("preprocess", preprocess()), ("model", est)])
        model.fit(x.iloc[train_i], y.iloc[train_i])
        fitted[name] = model
        validation[name] = metrics(
            y.iloc[val_i], model.predict_proba(x.iloc[val_i])[:, 1], 0.5
        )
    best = max(
        (n for n in models if n != "prior_baseline"),
        key=lambda n: validation[n]["average_precision"],
    )
    model = fitted[best]
    val_p = model.predict_proba(x.iloc[val_i])[:, 1]
    thresholds = np.linspace(0.05, 0.95, 181)
    threshold = float(
        max(
            thresholds,
            key=lambda t: fbeta_score(
                y.iloc[val_i], val_p >= t, beta=2, zero_division=0
            ),
        )
    )
    # Models and threshold are frozen before any holdout evaluation. Do not refit here.
    test = {
        n: metrics(
            y.iloc[test_i],
            m.predict_proba(x.iloc[test_i])[:, 1],
            threshold if n == best else 0.5,
        )
        for n, m in fitted.items()
    }
    p = model.predict_proba(x.iloc[test_i])[:, 1]
    perm = permutation_importance(
        model,
        x.iloc[val_i],
        y.iloc[val_i],
        scoring="average_precision",
        n_repeats=5,
        random_state=42,
        n_jobs=2,
    )
    importance = sorted(
        [
            {"feature": f, "ap_drop": float(v), "std": float(s)}
            for f, v, s in zip(FEATURES, perm.importances_mean, perm.importances_std)
        ],
        key=lambda r: -r["ap_drop"],
    )
    precision, recall, pr_thresholds = precision_recall_curve(y.iloc[test_i], p)
    step = max(1, len(recall) // 100)
    summary = {
        "dataset": "IBM Telco Customer Churn sample",
        "dataset_sha256": hashlib.sha256(Path(csv_path).read_bytes()).hexdigest(),
        "rows": len(raw),
        "features": FEATURES,
        "churn_rate": float(y.mean()),
        "seed": 42,
        "split": {"train": len(train_i), "validation": len(val_i), "test": len(test_i)},
        "selected_model": best,
        "threshold": threshold,
        "selection_metric": "validation average precision",
        "threshold_metric": "validation F2",
        "validation": validation,
        "test": test,
        "importance": importance,
        "pr_curve": [
            {"recall": float(recall[i]), "precision": float(precision[i])}
            for i in range(0, len(recall), step)
        ],
        "versions": {
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
        },
        "limitations": [
            "Historical sample; no temporal validation or causal retention-effect estimate.",
            "Probabilities are uncalibrated; assess calibration before economic decisions.",
            "Sensitive/demographic fields excluded; no formal fairness audit or production drift study.",
        ],
    }
    cohort = x.iloc[test_i].copy()
    cohort["customerID"] = raw.customerID.iloc[test_i].values
    cohort["actual_churn"] = y.iloc[test_i].values
    cohort["risk_score"] = p
    cohort["flagged"] = p >= threshold
    cohort.sort_values("risk_score", ascending=False).to_csv(
        out / "holdout_scores.csv", index=False
    )
    joblib.dump(
        {"pipeline": model, "threshold": threshold, "features": FEATURES},
        out / "model.joblib",
    )
    (out / "metrics.json").write_text(json.dumps(summary, indent=2))
    (out / "split_ids.json").write_text(
        json.dumps(
            {
                k: raw.customerID.iloc[v].tolist()
                for k, v in [
                    ("train", train_i),
                    ("validation", val_i),
                    ("test", test_i),
                ]
            }
        )
    )
    return summary


def score(frame, bundle):
    x = validate(frame)
    p = bundle["pipeline"].predict_proba(x)[:, 1]
    return [
        {
            "risk_score": float(v),
            "flagged": bool(v >= bundle["threshold"]),
            "threshold": bundle["threshold"],
        }
        for v in p
    ]
