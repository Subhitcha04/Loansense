from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.connection import get_db

router = APIRouter()


@router.get("/portfolio", response_model=dict)
def get_portfolio(db: Session = Depends(get_db)):
    """
    Aggregate portfolio stats:
    total disbursed, active loans, collection rate, default rate,
    average risk score, disbursement by purpose.
    """
    totals = db.execute(text("""
        SELECT
            COUNT(*) as total_loans,
            SUM(principal) as total_disbursed,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_loans,
            SUM(CASE WHEN status = 'defaulted' THEN 1 ELSE 0 END) as defaulted_loans,
            SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_loans
        FROM loans
    """)).fetchone()

    avg_risk = db.execute(text("""
        SELECT AVG(risk_score) FROM loan_applications WHERE risk_score IS NOT NULL
    """)).scalar()

    # Collection rate this month: paid / (paid + overdue)
    collection = db.execute(text("""
        SELECT
            SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count,
            SUM(CASE WHEN status = 'overdue' THEN 1 ELSE 0 END) as overdue_count,
            COUNT(*) as total_due
        FROM repayment_schedules
        WHERE MONTH(due_date) = MONTH(CURDATE())
          AND YEAR(due_date) = YEAR(CURDATE())
    """)).fetchone()

    paid_count = collection[0] or 0
    total_due = (collection[0] or 0) + (collection[1] or 0)
    collection_rate = round(paid_count / total_due * 100, 1) if total_due > 0 else 0.0

    # Default rate
    total = totals[0] or 1
    default_rate = round((totals[3] or 0) / total * 100, 1)

    # Disbursements by purpose
    by_purpose = db.execute(text("""
        SELECT la.purpose, COUNT(*) as count, SUM(l.principal) as total
        FROM loans l JOIN loan_applications la ON l.application_id = la.id
        GROUP BY la.purpose
    """)).fetchall()

    # Weekly disbursements (last 8 weeks)
    weekly = db.execute(text("""
        SELECT
            YEARWEEK(disbursed_on, 1) as week,
            COUNT(*) as count,
            SUM(principal) as total
        FROM loans
        WHERE disbursed_on >= DATE_SUB(CURDATE(), INTERVAL 8 WEEK)
        GROUP BY YEARWEEK(disbursed_on, 1)
        ORDER BY week
    """)).fetchall()

    return {
        "total_loans": totals[0] or 0,
        "total_disbursed": float(totals[1] or 0),
        "active_loans": totals[2] or 0,
        "defaulted_loans": totals[3] or 0,
        "closed_loans": totals[4] or 0,
        "collection_rate": collection_rate,
        "default_rate": default_rate,
        "average_risk_score": round(float(avg_risk or 0), 4),
        "disbursement_by_purpose": [
            {"purpose": r[0], "count": r[1], "total": float(r[2] or 0)}
            for r in by_purpose
        ],
        "weekly_disbursements": [
            {"week": str(r[0]), "count": r[1], "total": float(r[2] or 0)}
            for r in weekly
        ]
    }


@router.get("/risk-distribution", response_model=dict)
def get_risk_distribution(db: Session = Depends(get_db)):
    """Breakdown of loan portfolio by risk tier."""
    rows = db.execute(text("""
        SELECT la.risk_tier, COUNT(*) as count, SUM(l.principal) as total_principal
        FROM loans l
        JOIN loan_applications la ON l.application_id = la.id
        WHERE la.risk_tier IS NOT NULL
        GROUP BY la.risk_tier
    """)).fetchall()

    total_loans = sum(r[1] for r in rows) or 1
    return {
        "distribution": [
            {
                "tier": r[0],
                "count": r[1],
                "total_principal": float(r[2] or 0),
                "percentage": round(r[1] / total_loans * 100, 1)
            }
            for r in rows
        ]
    }


@router.get("/repayment-trends", response_model=dict)
def get_repayment_trends(db: Session = Depends(get_db)):
    """Monthly collection efficiency: payments received vs expected."""
    rows = db.execute(text("""
        SELECT
            DATE_FORMAT(due_date, '%Y-%m') as month,
            SUM(emi_amount) as expected,
            SUM(CASE WHEN status = 'paid' THEN emi_amount ELSE 0 END) as collected,
            SUM(CASE WHEN status = 'overdue' THEN emi_amount ELSE 0 END) as overdue
        FROM repayment_schedules
        WHERE due_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY DATE_FORMAT(due_date, '%Y-%m')
        ORDER BY month
    """)).fetchall()

    return {
        "trends": [
            {
                "month": r[0],
                "expected": float(r[1] or 0),
                "collected": float(r[2] or 0),
                "overdue": float(r[3] or 0),
                "efficiency": round(float(r[2] or 0) / float(r[1] or 1) * 100, 1)
            }
            for r in rows
        ]
    }
