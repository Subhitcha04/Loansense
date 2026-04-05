from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import applicants, applications, loans, analytics, webhooks
from services.scheduler import start_scheduler

app = FastAPI(
    title="LoanSense API",
    description="""
    ## LoanSense — Intelligent Loan Origination & Risk Scoring Platform

    A full-stack fintech platform where borrowers apply for loans,
    and the system automatically scores their credit risk using an ML model,
    decides approval/rejection, generates a repayment schedule, tracks EMI
    payments, and fires event-driven webhooks.

    ### Key Features
    - **ML Risk Scoring** — XGBoost model predicts default probability (0–1)
    - **Risk-Based Pricing** — Interest rate auto-assigned by risk tier
    - **EMI Amortisation** — Full reducing-balance schedule generation
    - **Overdue Detection** — Daily APScheduler job, fires webhooks
    - **Webhook Delivery** — Retry with exponential backoff (0s → 5min → 30min)
    """,
    version="1.0.0",
    contact={"name": "LoanSense", "email": "admin@loansense.dev"},
    license_info={"name": "MIT"}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(applicants.router, prefix="/applicants", tags=["Applicants"])
app.include_router(applications.router, prefix="/applications", tags=["Applications"])
app.include_router(loans.router, prefix="/loans", tags=["Loans"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])


@app.on_event("startup")
def startup_event():
    start_scheduler()
    print("[LoanSense] API started. Visit /docs for Swagger UI.")


@app.get("/", tags=["Health"])
def health_check():
    return {
        "service": "LoanSense API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }
