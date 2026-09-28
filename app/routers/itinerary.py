import time
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
import httpx
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies import get_current_active_customer, log_usage
from app.models.customer import Customer
from app.core.config import get_settings

router = APIRouter(prefix="/v1/itinerary", tags=["itinerary"])
logger = logging.getLogger("roamwise_api")
settings = get_settings()

ACTIVITIES_PER_DAY = {"relaxed": 1, "moderate": 2, "packed": 3}

SYSTEM_PROMPT = (
    "You are a travel-itinerary planner for RoamWise. Given a destination, "
    "trip length and traveller count, produce a realistic day-by-day plan. "
    "Respond with ONLY valid JSON, no prose, no markdown fences, matching "
    "exactly this shape: "
    '{"days":[{"day":1,"label":"Arrival","morning":"...","afternoon":"...","evening":"...","notes":"..."}]}. '
    "One object per day, day numbers sequential starting at 1, exactly as "
    "many day objects as the requested duration. Be specific to the named "
    "destination — real neighbourhoods/landmarks where you're confident of "
    "them, sensible generic activity types where you're not. Do not state "
    "opening hours, prices or availability as fact — phrase anything like "
    "that as typical/approximate and say to verify it."
)


class ItineraryRequest(BaseModel):
    destination: str
    duration_days: int = Field(gt=0, le=30)
    travelers: int = Field(gt=0, le=50)
    pace: Optional[str] = Field(default="moderate", pattern="^(relaxed|moderate|packed)$")


def _skeleton_days(duration_days: int, pace: str):
    slots = ACTIVITIES_PER_DAY[pace]
    days = []
    for d in range(1, duration_days + 1):
        if d == 1:
            label = "Arrival"
        elif d == duration_days:
            label = "Departure"
        else:
            label = "Explore"
        days.append({
            "day": d,
            "label": label,
            "activity_slots": slots if label == "Explore" else max(1, slots - 1),
        })
    return days


async def _call_groq(prompt: str) -> Optional[list]:
    """Returns a list of day dicts from Groq, or None if unavailable/failed.
    Never raises — a provider hiccup degrades to the honest skeleton instead
    of a 500, mirroring how the main RoamWise Worker treats every AI
    provider as best-effort with a graceful fallback path."""
    if not settings.groq_api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.groq_model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 2000,
                    "response_format": {"type": "json_object"},
                },
            )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        days = parsed.get("days")
        if not isinstance(days, list) or not days:
            return None
        return days
    except Exception:
        logger.exception("Groq itinerary generation failed; falling back to structural skeleton")
        return None


@router.post("/generate")
async def generate_itinerary(
    body: ItineraryRequest,
    request: Request,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_active_customer),
):
    start = time.perf_counter()
    prompt = (
        f"Destination: {body.destination}\n"
        f"Duration: {body.duration_days} days\n"
        f"Travellers: {body.travelers}\n"
        f"Pace: {body.pace}"
    )
    ai_days = await _call_groq(prompt)

    if ai_days is not None:
        result = {
            "destination": body.destination,
            "duration_days": body.duration_days,
            "travelers": body.travelers,
            "pace": body.pace,
            "days": ai_days,
            "source": "ai",
            "model": settings.groq_model,
            "note": "AI-generated plan — treat specifics (hours, prices, availability) as a starting point to verify, not confirmed facts.",
        }
        status_code = 200
    else:
        result = {
            "destination": body.destination,
            "duration_days": body.duration_days,
            "travelers": body.travelers,
            "pace": body.pace,
            "days": _skeleton_days(body.duration_days, body.pace),
            "source": "fallback",
            "note": (
                "Structural skeleton only — AI generation isn't configured on this deployment (set GROQ_API_KEY)."
                if not settings.groq_api_key
                else "Structural skeleton only — AI generation failed for this request, showing the fallback instead of an error."
            ) + " Fill in destination-specific stops yourself or via /v1/budget and /v1/packing.",
        }
        status_code = 200

    log_usage(
        db, customer.id, "/v1/itinerary/generate", "POST", status_code,
        response_time_ms=(time.perf_counter() - start) * 1000,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return result
