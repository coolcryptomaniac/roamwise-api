from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies import require_admin
from app.core.security import generate_api_key, hash_api_key
from app.models.customer import Customer

router = APIRouter(prefix="/v1/admin", tags=["admin"])

TIER_QUOTAS = {"basic": 1000, "pro": 10000, "enterprise": 100000}


class CreateCustomerRequest(BaseModel):
    email: EmailStr
    company_name: str | None = None
    tier: str = Field(default="basic", pattern="^(basic|pro|enterprise)$")


@router.post("/customers", status_code=status.HTTP_201_CREATED)
def create_customer(
    body: CreateCustomerRequest,
    db: Session = Depends(get_db),
    _admin: Customer = Depends(require_admin),
):
    if db.query(Customer).filter(Customer.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A customer with this email already exists.")

    api_key = generate_api_key()
    customer = Customer(
        email=body.email,
        company_name=body.company_name,
        hashed_api_key=hash_api_key(api_key),
        tier=body.tier,
        is_active=True,
        is_admin=False,
        monthly_quota=TIER_QUOTAS[body.tier],
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    # The raw key is only ever available at creation time — we store only
    # its hash, so this response is the one and only chance to hand it out.
    return {
        "id": customer.id,
        "email": customer.email,
        "tier": customer.tier,
        "monthly_quota": customer.monthly_quota,
        "api_key": api_key,
        "warning": "Store this API key now — it cannot be retrieved again.",
    }
