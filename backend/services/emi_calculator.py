from datetime import date
from dateutil.relativedelta import relativedelta
from typing import List


def calculate_emi(principal: float, annual_rate: float, term_months: int) -> float:
    """
    Standard reducing balance EMI formula:
    EMI = P × r × (1+r)^n / ((1+r)^n - 1)
    where:
        P = principal
        r = monthly interest rate (annual_rate / 12 / 100)
        n = number of months
    """
    r = annual_rate / 12 / 100
    if r == 0:
        return round(principal / term_months, 2)
    emi = principal * r * (1 + r) ** term_months / ((1 + r) ** term_months - 1)
    return round(emi, 2)


def generate_schedule(
    principal: float,
    annual_rate: float,
    term_months: int,
    start_date: date
) -> List[dict]:
    """
    Generate full amortisation schedule.
    Each row shows: instalment number, due date, EMI amount,
    principal component, interest component, outstanding balance.
    """
    emi = calculate_emi(principal, annual_rate, term_months)
    r = annual_rate / 12 / 100
    balance = principal
    schedule = []

    for i in range(1, term_months + 1):
        interest = round(balance * r, 2)
        principal_component = round(emi - interest, 2)

        # Adjust final instalment for rounding errors
        if i == term_months:
            principal_component = round(balance, 2)
            emi_this = round(principal_component + interest, 2)
        else:
            emi_this = emi

        balance = round(balance - principal_component, 2)
        due_date = start_date + relativedelta(months=i)

        schedule.append({
            "instalment_no": i,
            "due_date": due_date,
            "emi_amount": emi_this,
            "principal_component": principal_component,
            "interest_component": interest,
            "outstanding_balance": max(balance, 0.0),
            "status": "upcoming"
        })

    return schedule
