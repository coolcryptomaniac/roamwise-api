import time
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies import get_current_active_customer, log_usage
from app.models.customer import Customer

router = APIRouter(prefix="/v1/budget", tags=["budget"])

# Illustrative per-day per-traveller spend in INR, by tier. These are planning
# estimates, not live prices — the response says so explicitly rather than
# implying real-time pricing we don't have.
DAILY_RATES_INR = {
    "budget": {"stay": 800, "food": 400, "local_transport": 200, "activities": 300},
    "mid":    {"stay": 2500, "food": 900, "local_transport": 500, "activities": 800},
    "luxury": {"stay": 8000, "food": 2500, "local_transport": 1500, "activities": 2500},
}


class BudgetRequest(BaseModel):
    destination: str
    duration_days: int = Field(gt=0, le=90)
    travelers: int = Field(gt=0, le=50)
    tier: str = Field(default="mid", pattern="^(budget|mid|luxury)$")


@router.post("/calculate")
def calculate_budget(
    body: BudgetRequest,
    request: Request,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_active_customer),
):
    start = time.perf_counter()
    rates = DAILY_RATES_INR[body.tier]
    breakdown = {
        k: round(v * body.duration_days * body.travelers) for k, v in rates.items()
    }
    total = sum(breakdown.values())

    result = {
        "destination": body.destination,
        "duration_days": body.duration_days,
        "travelers": body.travelers,
        "tier": body.tier,
        "breakdown_inr": breakdown,
        "total_inr": total,
        "per_traveller_inr": round(total / body.travelers),
        "note": "Planning estimate from typical per-day spend by tier — not live pricing for this specific destination or dates.",
    }

    log_usage(
        db, customer.id, "/v1/budget/calculate", "POST", 200,
        response_time_ms=(time.perf_counter() - start) * 1000,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return result
