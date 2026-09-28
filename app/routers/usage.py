from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies import get_current_active_customer
from app.models.customer import Customer
from app.models.usage import UsageLog

router = APIRouter(prefix="/v1/usage", tags=["usage"])


@router.get("/stats")
def usage_stats(
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_active_customer),
):
    return {
        "tier": customer.tier,
        "monthly_quota": customer.monthly_quota,
        "requests_used_this_month": customer.requests_used_this_month,
        "requests_remaining": max(0, customer.monthly_quota - customer.requests_used_this_month),
    }


@router.get("/breakdown")
def usage_breakdown(
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_active_customer),
):
    rows = (
        db.query(UsageLog.endpoint, UsageLog.status_code)
        .filter(UsageLog.customer_id == customer.id)
        .all()
    )
    by_endpoint = Counter(r.endpoint for r in rows)
    errors_by_endpoint = Counter(r.endpoint for r in rows if r.status_code >= 400)

    return {
        "total_requests": len(rows),
        "by_endpoint": dict(by_endpoint),
        "errors_by_endpoint": dict(errors_by_endpoint),
    }
