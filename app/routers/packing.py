import time
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies import get_current_active_customer, log_usage
from app.models.customer import Customer

router = APIRouter(prefix="/v1/packing", tags=["packing"])

BASE_ITEMS = ["Passport/ID + copies", "Phone charger", "Power bank", "Reusable water bottle",
              "Basic first-aid kit", "Toiletries", "Daypack"]

CLIMATE_ITEMS = {
    "cold": ["Thermal layers", "Insulated jacket", "Woolen socks", "Gloves", "Beanie/cap", "Moisturizer/lip balm"],
    "hot": ["Breathable cotton clothing", "Sunscreen (SPF 50+)", "Sunglasses", "Hat", "Electrolyte sachets"],
    "rainy": ["Rain jacket/poncho", "Quick-dry clothing", "Waterproof phone pouch", "Extra socks"],
    "mixed": ["Layered clothing", "Light jacket", "Compact umbrella"],
}

ACTIVITY_ITEMS = {
    "trekking": ["Trekking shoes", "Trekking poles", "Headlamp", "Energy bars"],
    "beach": ["Swimwear", "Flip-flops", "Beach towel", "Waterproof bag"],
    "business": ["Formal wear", "Laptop + charger", "Business cards"],
    "snow": ["Snow boots", "Waterproof gloves", "Snow goggles"],
}


class PackingRequest(BaseModel):
    destination: str
    duration_days: int = Field(gt=0, le=90)
    climate: str = Field(default="mixed", pattern="^(cold|hot|rainy|mixed)$")
    activities: Optional[List[str]] = None


@router.post("/list")
def packing_list(
    body: PackingRequest,
    request: Request,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_active_customer),
):
    start = time.perf_counter()
    items = list(BASE_ITEMS) + list(CLIMATE_ITEMS.get(body.climate, []))
    unmatched_activities = []
    for activity in (body.activities or []):
        key = activity.strip().lower()
        if key in ACTIVITY_ITEMS:
            items += ACTIVITY_ITEMS[key]
        else:
            unmatched_activities.append(activity)

    clothing_sets = max(2, min(body.duration_days, 7))  # cap laundry-cycle assumption at a week

    result = {
        "destination": body.destination,
        "duration_days": body.duration_days,
        "climate": body.climate,
        "recommended_clothing_sets": clothing_sets,
        "items": sorted(set(items)),
        "note": "Rule-based checklist by climate/activity, not destination-specific weather data.",
    }
    if unmatched_activities:
        result["unmatched_activities"] = unmatched_activities

    log_usage(
        db, customer.id, "/v1/packing/list", "POST", 200,
        response_time_ms=(time.perf_counter() - start) * 1000,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return result
