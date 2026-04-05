from pydantic import BaseModel
from enum import Enum
from datetime import date, datetime
from typing import Optional, List


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LoanStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    DEFAULTED = "defaulted"


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class LoanPurpose(str, Enum):
    EDUCATION = "education"
    PERSONAL = "personal"
    MEDICAL = "medical"
    BUSINESS = "business"


class ApplicationCreate(BaseModel):
    applicant_id: int
    amount: float
    term_months: int
    purpose: LoanPurpose
    idempotency_key: Optional[str] = None


class RiskAssessment(BaseModel):
    risk_score: float       # 0.0 to 1.0
    risk_tier: RiskTier
    interest_rate: float    # assigned based on tier
    recommended_action: str  # approve / review / reject
    feature_importances: Optional[dict] = None


class ApplicationResponse(BaseModel):
    id: int
    applicant_id: int
    amount: float
    term_months: int
    purpose: str
    risk_score: Optional[float]
    risk_tier: Optional[str]
    interest_rate: Optional[float]
    recommended_action: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationDecision(BaseModel):
    decision: str   # "approved" or "rejected"
    notes: Optional[str] = None


class EMIScheduleRow(BaseModel):
    instalment_no: int
    due_date: date
    emi_amount: float
    principal_component: float
    interest_component: float
    outstanding_balance: float
    status: str           # upcoming / paid / overdue
    paid_on: Optional[date] = None


class LoanResponse(BaseModel):
    id: int
    application_id: int
    applicant_id: int
    principal: float
    interest_rate: float
    term_months: int
    emi_amount: float
    disbursed_on: date
    status: str

    class Config:
        from_attributes = True


class LoanStatusResponse(BaseModel):
    loan_id: int
    status: str
    total_instalments: int
    paid_instalments: int
    overdue_instalments: int
    upcoming_instalments: int
    outstanding_principal: float
    next_due_date: Optional[date]
    next_emi_amount: Optional[float]


class PaymentResponse(BaseModel):
    message: str
    instalment_no: int
    amount_paid: float
    outstanding_balance: float
