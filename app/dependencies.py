from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.customer import Customer
from app.core.security import hash_api_key
from app.core.rate_limit import check_rate_limit, get_rate_limit_headers
from app.core.config import get_settings

settings = get_settings()
security_bearer = HTTPBearer(auto_error=False)

async def get_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db)
):
    """
    Extract and validate API key from header.
    Supports: Authorization: Bearer <key> or X-API-Key: <key>
    """
    api_key = None

    # Check Authorization header
    if credentials:
        api_key = credentials.credentials
    else:
        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Pass it via X-API-Key header or Authorization: Bearer <key>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate key
    hashed = hash_api_key(api_key)
    customer = db.query(Customer).filter(
        Customer.hashed_api_key == hashed,
        Customer.is_active == True
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
        )

    # Check monthly quota
    if customer.requests_used_this_month >= customer.monthly_quota:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly quota exceeded. Limit: {customer.monthly_quota}. Upgrade your plan.",
        )

    # Rate limiting
    allowed, remaining, reset_in = check_rate_limit(api_key, customer.tier)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {reset_in} seconds.",
            headers=get_rate_limit_headers(allowed, remaining, reset_in, customer.tier),
        )

    # Store rate limit headers for middleware to attach
    request.state.rate_limit_headers = get_rate_limit_headers(allowed, remaining, reset_in, customer.tier)
    request.state.customer = customer

    return customer

async def get_current_active_customer(customer: Customer = Depends(get_api_key)):
    if not customer.is_active:
        raise HTTPException(status_code=400, detail="Account inactive")
    return customer

async def require_admin(customer: Customer = Depends(get_current_active_customer)):
    if not customer.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return customer

def log_usage(db: Session, customer_id: int, endpoint: str, method: str, 
              status_code: int, response_time_ms: float = None,
              ip_address: str = None, user_agent: str = None, payload: str = None):
    """Log API usage for billing and analytics."""
    from app.models.usage import UsageLog
    log = UsageLog(
        customer_id=customer_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time_ms=response_time_ms,
        ip_address=ip_address,
        user_agent=user_agent,
        request_payload=payload,
    )
    db.add(log)

    # Increment customer counter
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        customer.requests_used_this_month += 1

    db.commit()
