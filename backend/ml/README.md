# ML Model Directory

## model.pkl

This directory should contain `model.pkl` — the trained XGBoost credit risk model.

### How to generate it

```bash
cd backend
pip install -r requirements.txt
python ml/train.py
```

The script will:
1. Download the German Credit Dataset from UCI (or generate synthetic data as fallback)
2. Train and compare Logistic Regression, Random Forest, and XGBoost
3. Save the best model (XGBoost) as `model.pkl`
4. Save evaluation metrics as `evaluation_results.json`

### Why model.pkl is not committed

The trained model file is excluded from version control (`.gitignore`) because:
- It can be regenerated deterministically by running `train.py`
- Binary files bloat git history
- The training script itself is the source of truth

### Fallback

If `model.pkl` is missing, the API falls back to a transparent heuristic scoring
function in `services/risk_engine.py` so the platform remains fully functional
for demonstration purposes.
