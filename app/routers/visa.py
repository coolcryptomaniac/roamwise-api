import time
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies import get_current_active_customer, log_usage
from app.models.customer import Customer

router = APIRouter(prefix="/v1/visa", tags=["visa"])

# Small, honestly-scoped starter set. Visa rules change often and carry real
# consequences if wrong, so an unlisted pair returns a clear "not covered"
# response rather than a guessed answer.
VISA_GUIDES = {
    ("IN", "TH"): {
        "visa_required": False,
        "notes": "Visa-exempt for short tourist stays for Indian passport holders (duration subject to current bilateral policy).",
        "documents": ["Passport (6+ months validity)", "Return ticket", "Proof of accommodation", "Sufficient funds proof"],
    },
    ("IN", "AE"): {
        "visa_required": True,
        "notes": "E-visa required; typically processed online in a few days.",
        "documents": ["Passport (6+ months validity)", "Passport photo", "Confirmed return ticket", "Hotel booking"],
    },
    ("IN", "SG"): {
        "visa_required": True,
        "notes": "E-visa required for Indian passport holders.",
        "documents": ["Passport (6+ months validity)", "Passport photo", "Travel itinerary", "Proof of funds"],
    },
}


class VisaRequest(BaseModel):
    nationality: str  # ISO 3166-1 alpha-2, e.g. "IN"
    destination_country: str  # ISO 3166-1 alpha-2, e.g. "TH"


@router.post("/guide")
def visa_guide(
    body: VisaRequest,
    request: Request,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_active_customer),
):
    start = time.perf_counter()
    key = (body.nationality.strip().upper(), body.destination_country.strip().upper())
    guide = VISA_GUIDES.get(key)

    if guide:
        result = {"nationality": key[0], "destination_country": key[1], **guide,
                   "disclaimer": "Verify against the destination's official visa portal before booking — requirements change."}
        status_code = 200
    else:
        result = {
            "nationality": key[0], "destination_country": key[1],
            "covered": False,
            "message": "This nationality/destination pair isn't in our current guide set yet. Check the destination country's official immigration portal.",
        }
        status_code = 200  # honest empty result, not an error

    log_usage(
        db, customer.id, "/v1/visa/guide", "POST", status_code,
        response_time_ms=(time.perf_counter() - start) * 1000,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return result
