from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy import text

Base = declarative_base()

def ensure_schema_compatibility(db_engine):
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    with db_engine.connect() as conn:
        try:
            tables = [r[0] for r in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()]
            if "case_events" in tables:
                columns = [row[1] for row in conn.execute(text("PRAGMA table_info(case_events)")).fetchall()]
                if "confidence" not in columns:
                    conn.execute(text("ALTER TABLE case_events ADD COLUMN confidence FLOAT DEFAULT 1.0"))
                if "is_allegation" not in columns:
                    conn.execute(text("ALTER TABLE case_events ADD COLUMN is_allegation BOOLEAN DEFAULT 0"))
                if "attribution_status" not in columns:
                    conn.execute(text("ALTER TABLE case_events ADD COLUMN attribution_status VARCHAR DEFAULT 'ESTABLISHED'"))
                if "start_date" not in columns:
                    conn.execute(text("ALTER TABLE case_events ADD COLUMN start_date VARCHAR"))
                if "end_date" not in columns:
                    conn.execute(text("ALTER TABLE case_events ADD COLUMN end_date VARCHAR"))
                conn.commit()
        except Exception:
            pass

ensure_schema_compatibility(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
