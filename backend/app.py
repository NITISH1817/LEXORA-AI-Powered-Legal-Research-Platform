from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.config import settings
from backend.database import engine, Base, get_db

from backend.routes.api import router as api_router
from backend.routes.auth import router as auth_router

# Phase 10: import document_intel models to ensure tables are created
import backend.models.document_intel  # noqa: F401

# Create database tables (in production, use Alembic migrations)
Base.metadata.create_all(bind=engine)

# Validate critical security configuration on startup in production
from backend.security import get_secret_key
if settings.ENVIRONMENT.lower() == "production":
    get_secret_key()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Backend for the AI Legal Intelligence Workbench"
)

# Parse CORS origins from settings
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import time
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lexora")

@app.middleware("http")
async def add_security_headers_and_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Process request
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request {request_id} failed: {str(e)}")
        raise e
        
    process_time = time.time() - start_time
    
    # Add Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Request-ID"] = request_id
    
    # Log latency
    if request.url.path != "/health":
        logger.info(f"[{request_id}] {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
        
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}")
    content = {"message": "Internal server error."}
    if getattr(settings, "ENVIRONMENT", "development") != "production":
        content["details"] = str(exc)
        
    return JSONResponse(
        status_code=500,
        content=content,
    )

import os

@app.on_event("startup")
def startup_diagnostics():
    """Outputs secure operational startup diagnostics without exposing sensitive credentials."""
    logger.info("==================================================")
    logger.info(f"Starting {settings.PROJECT_NAME} (Env: {settings.ENVIRONMENT})")
    logger.info(f"Database: {settings.DATABASE_URL.split('://')[0]}://***")
    logger.info(f"CORS Allowed Origins: {settings.CORS_ORIGINS}")
    logger.info(f"Storage Paths: uploads={settings.UPLOAD_DIR}, processed={settings.PROCESSED_DIR}, monitoring={settings.PILOT_MONITORING_DIR}")
    logger.info(f"Pilot Monitoring: enabled={settings.PILOT_MONITORING_ENABLED}, log_queries={settings.PILOT_MONITORING_LOG_QUERIES}, retention={settings.PILOT_MONITORING_RETENTION_DAYS}d")
    ai_status = "READY (Gemini configured)" if settings.GEMINI_API_KEY else "DEGRADED (No GEMINI_API_KEY; search & evaluation operational)"
    logger.info(f"AI Synthesis Provider: {ai_status}")
    logger.info("==================================================")

@app.get("/health")
def health_check():
    """Liveness probe: verifies process is alive and responding."""
    return {"status": "ok", "project": settings.PROJECT_NAME}

@app.get("/health/ready")
def health_ready(db: Session = Depends(get_db)):
    """
    Readiness probe: verifies database connectivity, storage writability, and AI provider status.
    Distinguishes fully ready vs degraded mode (e.g. AI unconfigured) vs unavailable (DB/storage down).
    Never exposes credentials or internal keys.
    """
    components = {}
    is_healthy = True

    # 1. Database check
    try:
        db.execute(text("SELECT 1"))
        components["database"] = {"status": "connected"}
    except Exception as e:
        logger.error(f"Readiness check - database failure: {e}")
        components["database"] = {"status": "unavailable", "error": "Database connection failed."}
        is_healthy = False

    # 2. Persistent Storage check
    storage_dirs = [settings.UPLOAD_DIR, settings.PROCESSED_DIR, settings.PILOT_MONITORING_DIR]
    storage_ok = True
    for s_dir in storage_dirs:
        try:
            os.makedirs(s_dir, exist_ok=True)
            # Test write ability
            test_file = os.path.join(s_dir, ".health_check_probe")
            with open(test_file, "w") as f:
                f.write("probe")
            if os.path.exists(test_file):
                os.remove(test_file)
        except Exception as e:
            logger.error(f"Readiness check - storage directory '{s_dir}' unwritable: {e}")
            storage_ok = False
            break

    if storage_ok:
        components["storage"] = {"status": "writable"}
    else:
        components["storage"] = {"status": "unwritable", "error": "Storage volume permission or path failure."}
        is_healthy = False

    # 3. AI Synthesis provider status
    if settings.GEMINI_API_KEY:
        components["ai_synthesis"] = {"status": "configured"}
    else:
        components["ai_synthesis"] = {
            "status": "degraded",
            "message": "AI synthesis key not configured; hybrid search, comparison, and evaluation remain available."
        }

    # Failure case: essential dependency down -> HTTP 503
    if not is_healthy:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "components": components,
                "project": settings.PROJECT_NAME
            }
        )

    # Degraded case: essential dependencies ready, but AI unconfigured -> HTTP 200 with degraded flag
    overall_status = "ready" if settings.GEMINI_API_KEY else "degraded"
    return {
        "status": overall_status,
        "components": components,
        "project": settings.PROJECT_NAME
    }

from backend.routes.api import router as api_router
from backend.routes.auth import router as auth_router
from backend.routes.cases import router as cases_router
from backend.routes.compare import router as compare_router
from backend.routes.research import router as research_router
from backend.routes.evaluation import router as evaluation_router
from backend.routes.documents import router as documents_router

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(api_router, prefix="/api", tags=["search"])
app.include_router(cases_router, prefix="/api/cases", tags=["cases"])
app.include_router(compare_router, prefix="/api/compare", tags=["compare"])
app.include_router(research_router)
app.include_router(evaluation_router)
app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
