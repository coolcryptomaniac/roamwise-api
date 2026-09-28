import time
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies import get_current_active_customer, log_usage
from app.models.customer import Customer

router = APIRouter(prefix="/v1/itinerary", tags=["itinerary"])


class ItineraryRequest(BaseModel):
    destination: str
    duration_days: int = Field(gt=0, le=30)
    travelers: int = Field(gt=0, le=50)
    pace: Optional[str] = Field(default="moderate", pattern="^(relaxed|moderate|packed)$")


ACTIVITIES_PER_DAY = {"relaxed": 1, "moderate": 2, "packed": 3}


@router.post("/generate")
def generate_itinerary(
    body: ItineraryRequest,
    request: Request,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_active_customer),
):
    """
    Generates a structural day-by-day skeleton (arrival/explore/departure
    shape, slot count by pace). This is template scaffolding, not an
    AI-written, destination-researched plan — we don't have a live AI
    itinerary model wired into this API yet, and would rather say that
    plainly than return content that reads as researched but isn't.
    """
    start = time.perf_counter()
    slots = ACTIVITIES_PER_DAY[body.pace]
    days = []
    for d in range(1, body.duration_days + 1):
        if d == 1:
            label = "Arrival"
        elif d == body.duration_days:
            label = "Departure"
        else:
            label = "Explore"
        days.append({
            "day": d,
            "label": label,
            "activity_slots": slots if label == "Explore" else max(1, slots - 1),
        })

    result = {
        "destination": body.destination,
        "duration_days": body.duration_days,
        "travelers": body.travelers,
        "pace": body.pace,
        "days": days,
        "note": "Structural skeleton only — fill in destination-specific stops yourself or via /v1/budget and /v1/packing for the rest of the trip. Real AI-generated day content isn't wired into this API yet.",
    }

    log_usage(
        db, customer.id, "/v1/itinerary/generate", "POST", 200,
        response_time_ms=(time.perf_counter() - start) * 1000,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return result
