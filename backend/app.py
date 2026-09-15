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

@app.get("/health")
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

@app.get("/health/ready")
def health_ready(db: Session = Depends(get_db)):
    try:
        # Check DB connection
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "database unavailable"})

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
