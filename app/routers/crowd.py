from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.dependencies import get_current_active_customer
from app.models.customer import Customer

router = APIRouter(prefix="/v1/crowd", tags=["crowd"])


class CrowdRequest(BaseModel):
    destination: str
    date: str


@router.post("/forecast")
def crowd_forecast(
    body: CrowdRequest,
    customer: Customer = Depends(get_current_active_customer),
):
    """
    Crowd forecasting needs a real historical-footfall or live-signal data
    source, which isn't wired into this API. Returning invented numbers
    would be worse than returning nothing — a paying customer could route
    a client around a "dodge route" that doesn't correspond to anything
    real. So this is honestly 501 until a real data source is connected,
    not a fabricated 200.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Crowd forecasting isn't live yet — no verified crowd-data source is connected. "
               "We don't return estimated numbers for this endpoint because we can't back them with real data.",
    )
