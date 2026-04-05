from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.connection import get_db
from models.applicant import ApplicantCreate, ApplicantResponse, ApplicantSummary
from datetime import datetime

router = APIRouter()


@router.post("/", response_model=dict, status_code=201)
def create_applicant(applicant: ApplicantCreate, db: Session = Depends(get_db)):
    """Register a new borrower."""
    # Check duplicate email
    existing = db.execute(
        text("SELECT id FROM applicants WHERE email = :email"),
        {"email": applicant.email}
    ).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    result = db.execute(
        text("""
            INSERT INTO applicants (name, email, income, employment_years,
                existing_loans, debt_to_income, credit_history_years)
            VALUES (:name, :email, :income, :employment_years,
                :existing_loans, :debt_to_income, :credit_history_years)
        """),
        applicant.model_dump()
    )
    db.commit()
    applicant_id = result.lastrowid

    row = db.execute(
        text("SELECT * FROM applicants WHERE id = :id"), {"id": applicant_id}
    ).fetchone()

    return {
        "id": row[0], "name": row[1], "email": row[2],
        "income": float(row[3]), "employment_years": row[4],
        "existing_loans": row[5], "debt_to_income": row[6],
        "credit_history_years": row[7], "created_at": str(row[8])
    }


@router.get("/{applicant_id}", response_model=dict)
def get_applicant(applicant_id: int, db: Session = Depends(get_db)):
    """Fetch applicant profile with credit summary."""
    row = db.execute(
        text("SELECT * FROM applicants WHERE id = :id"), {"id": applicant_id}
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Applicant not found")

    # Credit summary
    apps = db.execute(
        text("SELECT COUNT(*) FROM loan_applications WHERE applicant_id = :id"),
        {"id": applicant_id}
    ).scalar()

    active_loans = db.execute(
        text("SELECT COUNT(*) FROM loans WHERE applicant_id = :id AND status = 'active'"),
        {"id": applicant_id}
    ).scalar()

    outstanding = db.execute(
        text("""
            SELECT COALESCE(SUM(rs.outstanding_balance), 0)
            FROM repayment_schedules rs
            JOIN loans l ON rs.loan_id = l.id
            WHERE l.applicant_id = :id AND rs.status = 'upcoming'
              AND rs.instalment_no = (
                SELECT MIN(instalment_no) FROM repayment_schedules
                WHERE loan_id = rs.loan_id AND status = 'upcoming'
              )
        """),
        {"id": applicant_id}
    ).scalar()

    return {
        "id": row[0], "name": row[1], "email": row[2],
        "income": float(row[3]), "employment_years": row[4],
        "existing_loans": row[5], "debt_to_income": row[6],
        "credit_history_years": row[7], "created_at": str(row[8]),
        "summary": {
            "total_applications": apps,
            "active_loans": active_loans,
            "total_outstanding": float(outstanding or 0)
        }
    }


@router.get("/", response_model=list)
def list_applicants(db: Session = Depends(get_db)):
    """List all applicants."""
    rows = db.execute(text("SELECT * FROM applicants ORDER BY created_at DESC")).fetchall()
    return [
        {
            "id": r[0], "name": r[1], "email": r[2],
            "income": float(r[3]), "employment_years": r[4],
            "existing_loans": r[5], "debt_to_income": r[6],
            "credit_history_years": r[7], "created_at": str(r[8])
        }
        for r in rows
    ]
