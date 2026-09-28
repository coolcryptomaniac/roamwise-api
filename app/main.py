import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.db.base import Base, engine
from app.routers import itinerary, crowd, budget, packing, visa, usage, admin

logger = logging.getLogger("roamwise_api")

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup if needed
    pass

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=settings.description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS — this API is authenticated via an API key header (X-API-Key /
# Authorization: Bearer), never cookies, so allow_credentials must stay
# False. allow_origins=["*"] + allow_credentials=True is an invalid CORS
# combination anyway (rejected by spec-compliant browsers), and pairing a
# wildcard origin with credentialed requests is the classic misconfig that
# lets any site ride a signed-in user's session — moot here since we never
# send credentials, but keeping allow_credentials=False makes that explicit
# rather than accidental.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach rate limit headers middleware
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    response = await call_next(request)
    if hasattr(request.state, "rate_limit_headers"):
        for key, value in request.state.rate_limit_headers.items():
            response.headers[key] = str(value)
    return response

# Global exception handler — log the real error server-side, but never hand
# an unauthenticated caller str(exc): a DB error can contain table/column
# names, an httpx error can contain an internal URL, a validation error can
# echo request internals. Every endpoint here is reachable pre-auth (the
# handler fires before/around dependency errors too), so this is externally
# visible surface, not just a dev convenience.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

# Include routers
app.include_router(itinerary.router)
app.include_router(crowd.router)
app.include_router(budget.router)
app.include_router(packing.router)
app.include_router(visa.router)
app.include_router(usage.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": settings.version,
        "description": settings.description,
        "docs": "/docs",
        "status": "operational",
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": __import__("datetime").datetime.now().isoformat()}

@app.get("/v1/pricing")
def get_pricing():
    """Public endpoint to view API pricing tiers."""
    return {
        "tiers": [
            {
                "name": "Basic",
                "price": "₹999/month",
                "requests": "1,000/month",
                "rate_limit": "20/minute",
                "features": ["Itinerary generation", "Budget calculator", "Packing lists", "Email support"],
            },
            {
                "name": "Pro",
                "price": "₹4,999/month",
                "requests": "10,000/month",
                "rate_limit": "100/minute",
                "features": ["All Basic features", "Crowd forecasts", "Visa guides", "Priority support", "Usage analytics"],
            },
            {
                "name": "Enterprise",
                "price": "₹24,999/month",
                "requests": "100,000/month",
                "rate_limit": "500/minute",
                "features": ["All Pro features", "Custom endpoints", "Dedicated account manager", "SLA guarantee", "White-label options"],
            },
        ],
        "notes": [
            "All prices in INR, inclusive of GST",
            "Pay-as-you-go overage: ₹1 per request beyond quota",
            "Annual plans: 2 months free",
            "Custom enterprise pricing available for >500K requests/month",
        ],
    }
