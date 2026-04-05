from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.connection import get_db
from models.loan import ApplicationCreate, ApplicationDecision
from services.risk_engine import score
from services.webhook_dispatcher import dispatch
import uuid

router = APIRouter()


def _run_scoring(application_id: int, applicant_id: int,
                 loan_amount: float, term_months: int):
    """Background task: run ML scoring and update application."""
    from db.connection import SessionLocal
    db = SessionLocal()
    try:
        applicant = db.execute(
            text("SELECT * FROM applicants WHERE id = :id"), {"id": applicant_id}
        ).fetchone()

        if not applicant:
            return

        features = {
            "income": float(applicant[3]),
            "employment_years": float(applicant[4]),
            "loan_amount": loan_amount,
            "term_months": term_months,
            "debt_to_income": float(applicant[6]),
            "existing_loans": int(applicant[5]),
            "credit_history_years": float(applicant[7]),
        }

        result = score(features)

        db.execute(
            text("""
                UPDATE loan_applications
                SET risk_score = :risk_score, risk_tier = :risk_tier,
                    interest_rate = :interest_rate,
                    recommended_action = :recommended_action
                WHERE id = :id
            """),
            {
                "risk_score": result["risk_score"],
                "risk_tier": result["risk_tier"],
                "interest_rate": result["interest_rate"],
                "recommended_action": result["recommended_action"],
                "id": application_id
            }
        )

        # Store in risk_assessments table
        import json
        fi = result.get("feature_importances")
        fi_json = json.dumps(fi) if fi else None
        db.execute(
            text("""
                INSERT INTO risk_assessments
                (application_id, risk_score, risk_tier, interest_rate,
                 recommended_action, feature_importances)
                VALUES (:app_id, :rs, :rt, :ir, :ra, :fi)
            """),
            {
                "app_id": application_id,
                "rs": result["risk_score"],
                "rt": result["risk_tier"],
                "ir": result["interest_rate"],
                "ra": result["recommended_action"],
                "fi": fi_json
            }
        )
        db.commit()

        dispatch("application.scored", {
            "application_id": application_id,
            "risk_score": result["risk_score"],
            "risk_tier": result["risk_tier"],
            "recommended_action": result["recommended_action"]
        })
    except Exception as e:
        print(f"[Scoring] Error: {e}")
    finally:
        db.close()


@router.post("/", response_model=dict, status_code=202)
def submit_application(
    application: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Submit a loan application. Triggers ML scoring asynchronously."""
    # Verify applicant exists
    applicant = db.execute(
        text("SELECT id FROM applicants WHERE id = :id"),
        {"id": application.applicant_id}
    ).fetchone()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

    # Idempotency check
    idem_key = application.idempotency_key or str(uuid.uuid4())
    existing = db.execute(
        text("SELECT id FROM loan_applications WHERE idempotency_key = :key"),
        {"key": idem_key}
    ).fetchone()
    if existing:
        row = db.execute(
            text("SELECT * FROM loan_applications WHERE id = :id"),
            {"id": existing[0]}
        ).fetchone()
        return _format_application(row)

    result = db.execute(
        text("""
            INSERT INTO loan_applications
            (applicant_id, amount, term_months, purpose, idempotency_key)
            VALUES (:applicant_id, :amount, :term_months, :purpose, :idempotency_key)
        """),
        {
            "applicant_id": application.applicant_id,
            "amount": application.amount,
            "term_months": application.term_months,
            "purpose": application.purpose.value,
            "idempotency_key": idem_key
        }
    )
    db.commit()
    application_id = result.lastrowid

    # Trigger ML scoring in background
    background_tasks.add_task(
        _run_scoring,
        application_id,
        application.applicant_id,
        application.amount,
        application.term_months
    )

    row = db.execute(
        text("SELECT * FROM loan_applications WHERE id = :id"),
        {"id": application_id}
    ).fetchone()

    return {**_format_application(row), "message": "Application submitted. Scoring in progress."}


@router.get("/{application_id}", response_model=dict)
def get_application(application_id: int, db: Session = Depends(get_db)):
    """Get application status, risk score, tier and reason codes."""
    row = db.execute(
        text("SELECT * FROM loan_applications WHERE id = :id"),
        {"id": application_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")

    result = _format_application(row)

    # Attach feature importances from risk_assessments
    ra = db.execute(
        text("SELECT feature_importances FROM risk_assessments WHERE application_id = :id ORDER BY id DESC LIMIT 1"),
        {"id": application_id}
    ).fetchone()
    if ra and ra[0]:
        try:
            import json
            fi = ra[0]
            result["feature_importances"] = json.loads(fi) if isinstance(fi, str) else fi
        except Exception:
            result["feature_importances"] = {}

    return result


@router.post("/{application_id}/decision", response_model=dict)
def make_decision(
    application_id: int,
    decision: ApplicationDecision,
    db: Session = Depends(get_db)
):
    """Lender approves or rejects an application."""
    row = db.execute(
        text("SELECT * FROM loan_applications WHERE id = :id"),
        {"id": application_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")

    if row[10] != "pending":
        raise HTTPException(status_code=400,
                            detail=f"Application already {row[10]}")

    if decision.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")

    db.execute(
        text("UPDATE loan_applications SET status = :status WHERE id = :id"),
        {"status": decision.decision, "id": application_id}
    )
    db.commit()

    event_type = "loan.approved" if decision.decision == "approved" else "loan.rejected"
    dispatch(event_type, {"application_id": application_id, "decision": decision.decision})

    # Auto-create loan if approved
    if decision.decision == "approved" and row[4] is not None:
        _create_loan_from_application(application_id, row, db)

    return {"application_id": application_id, "status": decision.decision,
            "message": f"Application {decision.decision} successfully"}


def _create_loan_from_application(application_id: int, app_row, db: Session):
    """Internal: create a Loan + repayment schedule when application is approved."""
    from services.emi_calculator import calculate_emi, generate_schedule
    from datetime import date

    principal = float(app_row[2])
    interest_rate = float(app_row[6]) if app_row[6] else 13.0
    term_months = int(app_row[3])
    applicant_id = int(app_row[1])
    emi = calculate_emi(principal, interest_rate, term_months)
    today = date.today()

    result = db.execute(
        text("""
            INSERT INTO loans (application_id, applicant_id, principal,
                interest_rate, term_months, emi_amount, disbursed_on)
            VALUES (:app_id, :applicant_id, :principal, :interest_rate,
                :term_months, :emi_amount, :disbursed_on)
        """),
        {
            "app_id": application_id,
            "applicant_id": applicant_id,
            "principal": principal,
            "interest_rate": interest_rate,
            "term_months": term_months,
            "emi_amount": emi,
            "disbursed_on": today
        }
    )
    db.commit()
    loan_id = result.lastrowid

    schedule = generate_schedule(principal, interest_rate, term_months, today)
    for row in schedule:
        db.execute(
            text("""
                INSERT INTO repayment_schedules
                (loan_id, instalment_no, due_date, emi_amount,
                 principal_component, interest_component, outstanding_balance, status)
                VALUES (:loan_id, :instalment_no, :due_date, :emi_amount,
                 :principal_component, :interest_component, :outstanding_balance, :status)
            """),
            {"loan_id": loan_id, **{k: str(v) if hasattr(v, 'isoformat') else v
                                    for k, v in row.items()}}
        )
    db.commit()


@router.get("/", response_model=list)
def list_applications(db: Session = Depends(get_db)):
    """List all loan applications."""
    rows = db.execute(
        text("""
            SELECT la.*, a.name as applicant_name
            FROM loan_applications la
            JOIN applicants a ON la.applicant_id = a.id
            ORDER BY la.created_at DESC
        """)
    ).fetchall()
    return [
        {
            **_format_application(r),
            "applicant_name": r[12] if len(r) > 12 else None
        }
        for r in rows
    ]


def _format_application(row) -> dict:
    return {
        "id": row[0],
        "applicant_id": row[1],
        "amount": float(row[2]),
        "term_months": row[3],
        "purpose": row[4],
        "risk_score": float(row[5]) if row[5] is not None else None,
        "risk_tier": row[6],
        "interest_rate": float(row[7]) if row[7] is not None else None,
        "recommended_action": row[8],
        "status": row[10],
        "idempotency_key": row[11] if len(row) > 11 else None,
        "created_at": str(row[12] if len(row) > 12 else "")
    }
