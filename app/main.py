from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.db.base import Base, engine
from app.routers import itinerary, crowd, budget, packing, visa, usage, admin

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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
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

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc)},
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
