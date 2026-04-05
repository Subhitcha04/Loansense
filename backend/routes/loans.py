from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.connection import get_db
from services.webhook_dispatcher import dispatch
from datetime import date

router = APIRouter()


@router.get("/{loan_id}/schedule", response_model=list)
def get_schedule(loan_id: int, db: Session = Depends(get_db)):
    """Return full EMI amortisation schedule for a loan."""
    loan = db.execute(
        text("SELECT id FROM loans WHERE id = :id"), {"id": loan_id}
    ).fetchone()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    rows = db.execute(
        text("""
            SELECT id, instalment_no, due_date, emi_amount,
                   principal_component, interest_component,
                   outstanding_balance, status, paid_on
            FROM repayment_schedules
            WHERE loan_id = :loan_id
            ORDER BY instalment_no
        """),
        {"loan_id": loan_id}
    ).fetchall()

    return [
        {
            "id": r[0],
            "instalment_no": r[1],
            "due_date": str(r[2]),
            "emi_amount": float(r[3]),
            "principal_component": float(r[4]),
            "interest_component": float(r[5]),
            "outstanding_balance": float(r[6]),
            "status": r[7],
            "paid_on": str(r[8]) if r[8] else None
        }
        for r in rows
    ]


@router.post("/{loan_id}/pay", response_model=dict)
def make_payment(loan_id: int, db: Session = Depends(get_db)):
    """Mark the next upcoming EMI as paid."""
    loan = db.execute(
        text("SELECT id, applicant_id FROM loans WHERE id = :id"), {"id": loan_id}
    ).fetchone()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    # Get next unpaid instalment
    next_due = db.execute(
        text("""
            SELECT id, instalment_no, emi_amount, outstanding_balance
            FROM repayment_schedules
            WHERE loan_id = :loan_id AND status IN ('upcoming', 'overdue')
            ORDER BY instalment_no
            LIMIT 1
        """),
        {"loan_id": loan_id}
    ).fetchone()

    if not next_due:
        raise HTTPException(status_code=400, detail="No pending instalments. Loan may be fully paid.")

    schedule_id, instalment_no, emi_amount, outstanding_balance = next_due

    # Mark as paid
    db.execute(
        text("""
            UPDATE repayment_schedules
            SET status = 'paid', paid_on = :today
            WHERE id = :id
        """),
        {"today": date.today(), "id": schedule_id}
    )

    # Record payment
    db.execute(
        text("""
            INSERT INTO payments (loan_id, schedule_id, amount_paid)
            VALUES (:loan_id, :schedule_id, :amount_paid)
        """),
        {"loan_id": loan_id, "schedule_id": schedule_id, "amount_paid": float(emi_amount)}
    )
    db.commit()

    # Check if loan is fully paid
    remaining = db.execute(
        text("""
            SELECT COUNT(*) FROM repayment_schedules
            WHERE loan_id = :loan_id AND status IN ('upcoming', 'overdue')
        """),
        {"loan_id": loan_id}
    ).scalar()

    if remaining == 0:
        db.execute(
            text("UPDATE loans SET status = 'closed' WHERE id = :id"),
            {"id": loan_id}
        )
        db.commit()

    dispatch("payment.received", {
        "loan_id": loan_id,
        "instalment_no": instalment_no,
        "amount_paid": float(emi_amount),
        "remaining_instalments": remaining
    })

    return {
        "message": "Payment recorded successfully",
        "instalment_no": instalment_no,
        "amount_paid": float(emi_amount),
        "outstanding_balance": float(outstanding_balance),
        "remaining_instalments": remaining
    }


@router.get("/{loan_id}/status", response_model=dict)
def get_loan_status(loan_id: int, db: Session = Depends(get_db)):
    """Current loan health summary."""
    loan = db.execute(
        text("SELECT * FROM loans WHERE id = :id"), {"id": loan_id}
    ).fetchone()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    stats = db.execute(
        text("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid,
                SUM(CASE WHEN status = 'overdue' THEN 1 ELSE 0 END) as overdue,
                SUM(CASE WHEN status = 'upcoming' THEN 1 ELSE 0 END) as upcoming
            FROM repayment_schedules
            WHERE loan_id = :loan_id
        """),
        {"loan_id": loan_id}
    ).fetchone()

    next_due = db.execute(
        text("""
            SELECT due_date, emi_amount FROM repayment_schedules
            WHERE loan_id = :loan_id AND status IN ('upcoming', 'overdue')
            ORDER BY instalment_no LIMIT 1
        """),
        {"loan_id": loan_id}
    ).fetchone()

    # Outstanding principal = last upcoming outstanding balance
    outstanding = db.execute(
        text("""
            SELECT outstanding_balance FROM repayment_schedules
            WHERE loan_id = :loan_id AND status IN ('upcoming', 'overdue')
            ORDER BY instalment_no LIMIT 1
        """),
        {"loan_id": loan_id}
    ).scalar()

    return {
        "loan_id": loan_id,
        "status": loan[8],
        "total_instalments": stats[0],
        "paid_instalments": stats[1] or 0,
        "overdue_instalments": stats[2] or 0,
        "upcoming_instalments": stats[3] or 0,
        "outstanding_principal": float(outstanding or 0),
        "next_due_date": str(next_due[0]) if next_due else None,
        "next_emi_amount": float(next_due[1]) if next_due else None
    }


@router.get("/{loan_id}", response_model=dict)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    """Get loan details."""
    loan = db.execute(
        text("SELECT * FROM loans WHERE id = :id"), {"id": loan_id}
    ).fetchone()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    return {
        "id": loan[0], "application_id": loan[1], "applicant_id": loan[2],
        "principal": float(loan[3]), "interest_rate": float(loan[4]),
        "term_months": loan[5], "emi_amount": float(loan[6]),
        "disbursed_on": str(loan[7]), "status": loan[8]
    }


@router.get("/", response_model=list)
def list_loans(db: Session = Depends(get_db)):
    """List all loans."""
    rows = db.execute(
        text("""
            SELECT l.*, a.name as applicant_name
            FROM loans l JOIN applicants a ON l.applicant_id = a.id
            ORDER BY l.id DESC
        """)
    ).fetchall()
    return [
        {
            "id": r[0], "application_id": r[1], "applicant_id": r[2],
            "principal": float(r[3]), "interest_rate": float(r[4]),
            "term_months": r[5], "emi_amount": float(r[6]),
            "disbursed_on": str(r[7]), "status": r[8],
            "applicant_name": r[9] if len(r) > 9 else None
        }
        for r in rows
    ]
