"""
LoanSense — ML Model Training Script
=====================================
Trains and evaluates 3 models on the German Credit Dataset (UCI).
Downloads automatically via scikit-learn / urllib.

Run from backend/ml/ directory:
    python train.py

Outputs:
    model.pkl — best model (XGBoost) saved with joblib
    evaluation_results.json — metrics for all 3 models
"""

import os
import json
import warnings
import numpy as np
import pandas as pd
import joblib
from io import StringIO
from urllib.request import urlretrieve

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report
)
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────
# 1. Load Dataset
# ─────────────────────────────────────────

def load_german_credit():
    """
    Load German Credit Dataset from UCI repository.
    Falls back to synthetic data if download fails.
    """
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data"
    local_path = os.path.join(os.path.dirname(__file__), "german.data")

    try:
        if not os.path.exists(local_path):
            print("Downloading German Credit Dataset from UCI...")
            urlretrieve(url, local_path)
            print("Download complete.")

        col_names = [
            "checking_account", "duration", "credit_history", "purpose",
            "credit_amount", "savings", "employment", "installment_rate",
            "personal_status", "other_debtors", "residence_since",
            "property", "age", "other_installments", "housing",
            "existing_credits", "job", "num_dependents", "telephone",
            "foreign_worker", "target"
        ]
        df = pd.read_csv(local_path, sep=" ", header=None, names=col_names)
        # Target: 1 = good credit, 2 = bad credit → remap to 0/1 (1 = default)
        df["target"] = (df["target"] == 2).astype(int)
        print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"Default rate: {df['target'].mean():.1%}")
        return df

    except Exception as e:
        print(f"Could not download dataset: {e}")
        print("Generating synthetic dataset for demonstration...")
        return generate_synthetic_data()


def generate_synthetic_data(n=1000):
    """Generate synthetic loan data for demonstration when UCI is unavailable."""
    np.random.seed(42)
    income = np.random.normal(60000, 20000, n).clip(15000, 200000)
    employment_years = np.random.exponential(5, n).clip(0, 40)
    loan_amount = np.random.normal(150000, 80000, n).clip(10000, 500000)
    term_months = np.random.choice([12, 24, 36, 48, 60], n)
    debt_to_income = np.random.beta(2, 5, n)
    existing_loans = np.random.poisson(1, n).clip(0, 5)
    credit_history_years = np.random.exponential(7, n).clip(0, 40)

    # Default probability based on features
    default_prob = (
        0.05
        + 0.4 * debt_to_income
        + 0.05 * existing_loans
        - 0.01 * credit_history_years
        - 0.000003 * income
        + 0.003 * (loan_amount / income)
    ).clip(0.02, 0.95)
    target = np.random.binomial(1, default_prob)

    return pd.DataFrame({
        "income": income, "employment_years": employment_years,
        "loan_amount": loan_amount, "term_months": term_months,
        "debt_to_income": debt_to_income, "existing_loans": existing_loans,
        "credit_history_years": credit_history_years, "target": target
    })


# ─────────────────────────────────────────
# 2. Preprocessing
# ─────────────────────────────────────────

def preprocess(df: pd.DataFrame):
    """Encode categoricals, select features, return X, y."""
    target = df["target"].values

    # Select numeric or encode categorical columns
    feature_cols = []
    processed = pd.DataFrame()

    for col in df.columns:
        if col == "target":
            continue
        if df[col].dtype == object:
            le = LabelEncoder()
            processed[col] = le.fit_transform(df[col].astype(str))
        else:
            processed[col] = df[col]
        feature_cols.append(col)

    X = processed[feature_cols].values
    return X, target, feature_cols


# ─────────────────────────────────────────
# 3. Train & Evaluate
# ─────────────────────────────────────────

def evaluate_model(model, X_test, y_test, name):
    """Print and return evaluation metrics."""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "model": name,
        "accuracy":  round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall":    round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1":        round(f1_score(y_test, y_pred, zero_division=0), 4),
        "auc_roc":   round(roc_auc_score(y_test, y_prob), 4),
    }

    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    for k, v in metrics.items():
        if k != "model":
            print(f"  {k:12s}: {v}")
    print(classification_report(y_test, y_pred, target_names=["No Default", "Default"]))
    return metrics


def train():
    print("\n" + "="*60)
    print("  LoanSense — Credit Risk Model Training")
    print("="*60)

    # Load
    df = load_german_credit()
    X, y, feature_names = preprocess(df)

    print(f"\nFeatures ({len(feature_names)}): {feature_names}")
    print(f"Class balance — No Default: {(y==0).sum()}, Default: {(y==1).sum()}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    results = []
    best_model = None
    best_auc = 0

    # ── Model 1: Logistic Regression ──
    lr_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))
    ])
    lr_pipeline.fit(X_train, y_train)
    lr_metrics = evaluate_model(lr_pipeline, X_test, y_test, "Logistic Regression")
    results.append(lr_metrics)
    if lr_metrics["auc_roc"] > best_auc:
        best_auc = lr_metrics["auc_roc"]
        best_model = lr_pipeline

    # ── Model 2: Random Forest ──
    rf_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("clf", RandomForestClassifier(
            n_estimators=200, max_depth=8, class_weight="balanced",
            random_state=42, n_jobs=-1
        ))
    ])
    rf_pipeline.fit(X_train, y_train)
    rf_metrics = evaluate_model(rf_pipeline, X_test, y_test, "Random Forest")
    results.append(rf_metrics)
    if rf_metrics["auc_roc"] > best_auc:
        best_auc = rf_metrics["auc_roc"]
        best_model = rf_pipeline

    # ── Model 3: XGBoost ──
    try:
        from xgboost import XGBClassifier
        # Handle class imbalance
        scale_pos = (y_train == 0).sum() / (y_train == 1).sum()
        xgb_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("clf", XGBClassifier(
                n_estimators=300, max_depth=6, learning_rate=0.05,
                scale_pos_weight=scale_pos, use_label_encoder=False,
                eval_metric="auc", random_state=42, n_jobs=-1
            ))
        ])
        xgb_pipeline.fit(X_train, y_train)
        xgb_metrics = evaluate_model(xgb_pipeline, X_test, y_test, "XGBoost")
        results.append(xgb_metrics)
        if xgb_metrics["auc_roc"] > best_auc:
            best_auc = xgb_metrics["auc_roc"]
            best_model = xgb_pipeline
    except ImportError:
        print("\nXGBoost not installed. Skipping. Run: pip install xgboost")

    # ── Comparison Table ──
    print("\n" + "="*60)
    print("  MODEL COMPARISON TABLE")
    print("="*60)
    header = f"{'Model':<22} {'Accuracy':>9} {'Precision':>10} {'Recall':>8} {'F1':>8} {'AUC-ROC':>9}"
    print(header)
    print("-"*70)
    for r in results:
        print(f"{r['model']:<22} {r['accuracy']:>9} {r['precision']:>10} {r['recall']:>8} {r['f1']:>8} {r['auc_roc']:>9}")

    # ── Save Best Model ──
    output_path = os.path.join(os.path.dirname(__file__), "model.pkl")
    joblib.dump(best_model, output_path)
    print(f"\n✓ Best model saved to: {output_path}")
    print(f"  Best AUC-ROC: {best_auc:.4f}")

    # Save results JSON
    results_path = os.path.join(os.path.dirname(__file__), "evaluation_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"✓ Evaluation results saved to: {results_path}")

    return best_model, results


if __name__ == "__main__":
    train()
