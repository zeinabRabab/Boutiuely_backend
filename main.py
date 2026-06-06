"""
Boutiquely AI — Main FastAPI Application
========================================
Entry point for the AI-powered e-commerce backend.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

# Import all models so SQLAlchemy registers metadata before create_all
import models

from database.db import engine, Base
from routes import (
    auth_router,
    user_router,
    product_router,
    order_router,
    analytics_router,
    recommendation_router,
    report_router,
    monitoring_router,
)

# ── App Init ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Boutiquely AI API",
    description="AI-powered e-commerce backend with recommendations, analytics, and reporting",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
import os

# Configure allowed origins via environment for flexible local/dev setups.
# Set `ALLOWED_ORIGINS` env var as a comma-separated list (e.g. http://localhost:3000,http://127.0.0.1:5173)
# To allow any origin in development set ALLOWED_ORIGINS="*" (this will disable credentials).
env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    ALLOWED_ORIGINS = [o.strip() for o in env_origins.split(",") if o.strip()]
else:
    # sensible defaults used when no env var is provided
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://172.25.32.1:3000",
        "http://172.25.32.1:3002",
    ]

# If a wildcard is requested, disable credentials (browsers disallow '*' with credentials)
allow_credentials = True
allow_origins_arg = ALLOWED_ORIGINS
if len(ALLOWED_ORIGINS) == 1 and ALLOWED_ORIGINS[0] == "*":
    allow_origins_arg = ["*"]
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_arg,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Monitoring Middleware ─────────────────────────────────────────────
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """Log every API request to the monitoring system."""
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)

    try:
        from services.monitoring_service import log_api_request
        from database.db import SessionLocal
        db = SessionLocal()
        try:
            log_api_request(
                db=db,
                endpoint=str(request.url.path),
                method=request.method,
                status_code=response.status_code,
                duration_ms=duration_ms,
                ip_address=request.client.host if request.client else "unknown",
            )
        finally:
            db.close()
    except Exception:
        pass  # Never let monitoring break actual API calls

    return response


# ── Database Setup ─────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(product_router)
app.include_router(order_router)
app.include_router(analytics_router)
app.include_router(recommendation_router)
app.include_router(report_router)
app.include_router(monitoring_router)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Boutiquely AI API is running 🛍️✨"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "version": "2.0.0"}


# ── Auto-seed on first run ────────────────────────────────────────────────────
@app.on_event("startup")
async def auto_seed():
    """Auto-seed demo data on first startup if DB is empty."""
    from database.db import SessionLocal
    from models.user import User
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            try:
                from seed import seed
                seed()
            except Exception as e:
                print(f"⚠️  Auto-seed failed (non-critical): {e}")
    finally:
        db.close()


# ── Schema Migration Helper ────────────────────────────────────────────────────
@app.on_event("startup")
async def run_migrations():
    """Add new columns to existing databases without breaking existing data."""
    from sqlalchemy import text
    from database.db import engine
    with engine.connect() as conn:
        try:
            # Add alert_threshold if it doesn't exist
            conn.execute(text("ALTER TABLE products ADD COLUMN alert_threshold INTEGER NOT NULL DEFAULT 5"))
            conn.commit()
            print("✅ Migration: added alert_threshold column")
        except Exception:
            pass  # Column already exists