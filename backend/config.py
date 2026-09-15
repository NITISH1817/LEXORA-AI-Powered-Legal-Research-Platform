from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Legal Intelligence Workbench"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = "sqlite:///./legal_intel.db"
    ENVIRONMENT: str = "development"

    # Security / Auth
    SECRET_KEY: str = "change_this_to_a_secure_random_string_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS Config
    CORS_ORIGINS: str = "http://localhost:5173"

    # AI Config
    GEMINI_API_KEY: Optional[str] = None
    SEMANTIC_WEIGHT: float = 0.65
    KEYWORD_WEIGHT: float = 0.35

    # ----------------------------------------------------------------
    # Phase 10 — Document Ingestion Configuration
    # All values are configurable via environment variables.
    # Do NOT hardcode these elsewhere in the codebase.
    # ----------------------------------------------------------------

    # Upload limits
    MAX_FILE_SIZE_MB: int = 50                   # reject files larger than this

    # Allowed document formats (comma-separated)
    ALLOWED_EXTENSIONS: str = "pdf,docx,txt"

    # Chunking parameters
    CHUNK_SIZE: int = 400                         # max words per chunk
    CHUNK_OVERLAP: int = 2                        # overlap in sentences between chunks

    # Storage directories (replaceable without code changes)
    UPLOAD_DIR: str = "./storage/uploads"         # raw uploaded files
    PROCESSED_DIR: str = "./storage/processed"    # extracted pages / section cache

    # OCR support (off by default; set to True + install pytesseract to enable)
    OCR_ENABLED: bool = False

    # Lines per simulated page for .txt documents
    TXT_LINES_PER_PAGE: int = 50

    class Config:
        env_file = ".env"


settings = Settings()

