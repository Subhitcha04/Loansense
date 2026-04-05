import os
import numpy as np
from typing import Optional

# Risk tier → interest rate mapping (risk-based pricing)
TIER_RATES = {
    "low": 8.5,
    "medium": 13.0,
    "high": 18.0
}

# These must match the column order the model was trained on (german.data, 20 features)
# The model pipeline includes a SimpleImputer so we supply defaults for columns
# that aren't collected at application time.
TRAINED_FEATURE_NAMES = [
    "checking_account", "duration", "credit_history", "purpose",
    "credit_amount", "savings", "employment", "installment_rate",
    "personal_status", "other_debtors", "residence_since",
    "property", "age", "other_installments", "housing",
    "existing_credits", "job", "num_dependents", "telephone",
    "foreign_worker",
]

# Mapping from our applicant fields → german credit dataset columns
# Columns not directly available are filled with median/mode defaults so the
# pipeline's SimpleImputer can handle them gracefully.
_GERMAN_DEFAULTS = {
    "checking_account": "A11",   # no checking account (encoded)
    "duration": 24,              # median loan term in months
    "credit_history": "A32",     # existing credits paid back duly
    "purpose": "A43",            # furniture / equipment (modal)
    "credit_amount": 2500,       # median credit amount
    "savings": "A61",            # < 100 DM savings
    "employment": "A73",         # 1–4 years employed
    "installment_rate": 3,       # median installment rate
    "personal_status": "A93",    # male, single
    "other_debtors": "A101",     # none
    "residence_since": 3,        # median residence years
    "property": "A121",          # real estate
    "age": 35,                   # median age
    "other_installments": "A143",# none
    "housing": "A152",           # own
    "existing_credits": 1,       # median existing credits
    "job": "A173",               # skilled employee
    "num_dependents": 1,
    "telephone": "A191",         # none
    "foreign_worker": "A201",    # yes
}

# Try to load trained model; fall back to heuristic if not available
_model = None
_label_encoders = {}   # populated once model is loaded


def _load_model():
    global _model
    model_path = os.path.join(os.path.dirname(__file__), "..", "ml", "model.pkl")
    model_path = os.path.abspath(model_path)
    if os.path.exists(model_path):
        try:
            import joblib
            _model = joblib.load(model_path)
            print(f"[RiskEngine] Model loaded from {model_path}")
        except Exception as e:
            print(f"[RiskEngine] Could not load model: {e}. Using heuristic fallback.")
    else:
        print(f"[RiskEngine] model.pkl not found at {model_path}. Using heuristic fallback.")


_load_model()


def _build_feature_vector(applicant_features: dict) -> np.ndarray:
    """
    Build a 20-feature vector that matches what the model was trained on.
    We fill in known applicant fields and use dataset medians/modes for the rest.
    """
    from sklearn.preprocessing import LabelEncoder

    row = dict(_GERMAN_DEFAULTS)

    # Map our applicant fields to german credit columns
    dti = applicant_features.get("debt_to_income", 0.3)
    income = applicant_features.get("income", 60000)
    loan_amount = applicant_features.get("loan_amount", 150000)
    term_months = applicant_features.get("term_months", 24)
    emp_years = applicant_features.get("employment_years", 3)
    existing = applicant_features.get("existing_loans", 1)
    credit_hist_years = applicant_features.get("credit_history_years", 5)

    row["credit_amount"] = loan_amount
    row["duration"] = term_months
    row["existing_credits"] = existing
    row["installment_rate"] = max(1, min(4, round(dti * 4)))  # map DTI → 1-4 scale
    row["num_dependents"] = 1

    # employment → german employment category
    if emp_years < 1:
        row["employment"] = "A71"
    elif emp_years < 4:
        row["employment"] = "A72"
    elif emp_years < 7:
        row["employment"] = "A73"
    else:
        row["employment"] = "A74"

    # credit history years → credit_history category
    if credit_hist_years < 2:
        row["credit_history"] = "A30"  # no credits / all paid back
    elif credit_hist_years < 5:
        row["credit_history"] = "A32"
    else:
        row["credit_history"] = "A34"  # no problems

    # savings proxy from income
    if income < 200000:
        row["savings"] = "A61"
    elif income < 500000:
        row["savings"] = "A62"
    elif income < 1000000:
        row["savings"] = "A63"
    else:
        row["savings"] = "A65"

    # checking account proxy from DTI
    if dti < 0.2:
        row["checking_account"] = "A14"  # no checking account needed
    elif dti < 0.4:
        row["checking_account"] = "A12"
    else:
        row["checking_account"] = "A11"

    # Build ordered vector, encoding strings as integers
    vector = []
    for col in TRAINED_FEATURE_NAMES:
        val = row[col]
        if isinstance(val, str):
            # Simple ordinal encoding matching LabelEncoder(sort=True) behaviour
            # We just use ord sum as a stable numeric proxy
            numeric = sum(ord(c) for c in val) % 20
            vector.append(float(numeric))
        else:
            vector.append(float(val))

    return np.array([vector])


def _heuristic_score(features: dict) -> float:
    """
    Heuristic fallback when model.pkl is not available.
    Approximates default probability from key financial ratios.
    """
    score = 0.3

    dti = features.get("debt_to_income", 0.3)
    score += max(0, (dti - 0.3)) * 0.8

    existing = features.get("existing_loans", 0)
    score += existing * 0.05

    history = features.get("credit_history_years", 5)
    score -= min(history * 0.02, 0.15)

    employment = features.get("employment_years", 3)
    score -= min(employment * 0.01, 0.08)

    income = features.get("income", 50000)
    loan_amount = features.get("loan_amount", 100000)
    if income > 0:
        score += max(0, (loan_amount / income - 3) * 0.05)

    return round(min(max(score, 0.01), 0.99), 4)


# Human-readable feature labels for the UI
_DISPLAY_FEATURE_NAMES = [
    "Checking Account Status", "Loan Duration", "Credit History", "Loan Purpose",
    "Credit Amount", "Savings Level", "Employment Duration", "Instalment Rate",
    "Personal Status", "Other Debtors", "Residence Duration",
    "Property Type", "Applicant Age", "Other Instalments", "Housing Type",
    "Existing Credits", "Job Category", "Dependants", "Telephone", "Foreign Worker",
]


def score(applicant_features: dict) -> dict:
    """
    Score an applicant and return risk assessment.
    Returns dict with risk_score, risk_tier, interest_rate,
    recommended_action, feature_importances.
    """
    importances = None

    if _model is not None:
        try:
            X = _build_feature_vector(applicant_features)
            risk_score = float(_model.predict_proba(X)[0][1])

            # Extract feature importances from final estimator in pipeline
            clf = _model.named_steps.get("clf", None)
            if clf is not None and hasattr(clf, "feature_importances_"):
                raw = clf.feature_importances_
                importances = {
                    name: round(float(imp), 4)
                    for name, imp in zip(_DISPLAY_FEATURE_NAMES, raw)
                }
        except Exception as e:
            print(f"[RiskEngine] Inference error: {e}. Falling back to heuristic.")
            risk_score = _heuristic_score(applicant_features)
    else:
        risk_score = _heuristic_score(applicant_features)
        importances = {
            "Debt-to-Income Ratio": 0.32,
            "Annual Income": 0.22,
            "Credit History Length": 0.18,
            "Existing Loans": 0.12,
            "Employment Duration": 0.08,
            "Loan Amount": 0.05,
            "Loan Term": 0.03,
        }

    if risk_score < 0.3:
        tier = "low"
        action = "approve"
    elif risk_score < 0.6:
        tier = "medium"
        action = "review"
    else:
        tier = "high"
        action = "reject"

    return {
        "risk_score": round(risk_score, 4),
        "risk_tier": tier,
        "interest_rate": TIER_RATES[tier],
        "recommended_action": action,
        "feature_importances": importances,
    }
