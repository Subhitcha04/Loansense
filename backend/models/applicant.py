from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class ApplicantCreate(BaseModel):
    name: str
    email: str
    income: float
    employment_years: float
    existing_loans: int = 0
    debt_to_income: float
    credit_history_years: float


class ApplicantResponse(BaseModel):
    id: int
    name: str
    email: str
    income: float
    employment_years: float
    existing_loans: int
    debt_to_income: float
    credit_history_years: float
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicantSummary(BaseModel):
    id: int
    name: str
    email: str
    total_applications: int = 0
    active_loans: int = 0
    total_outstanding: float = 0.0
