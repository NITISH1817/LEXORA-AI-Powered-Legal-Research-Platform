import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from jose import JWTError, jwt
import bcrypt
from backend.config import settings

def get_secret_key() -> str:
    key = getattr(settings, "JWT_SECRET_KEY", None) or getattr(settings, "SECRET_KEY", None)
    if getattr(settings, "ENVIRONMENT", "development").lower() == "production":
        insecure_keys = {
            "change_this_to_a_secure_random_string_in_production",
            "super_secret_dev_key_change_me_in_prod",
            "secret", "jwt_secret", "changeme", ""
        }
        if not key or key in insecure_keys or len(key) < 32:
            raise ValueError("Insecure SECRET_KEY configured for production environment. A strong, random key of at least 32 characters is required.")
    return key or "super_secret_dev_key_change_me_in_prod"

SECRET_KEY = get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day
MAX_PASSWORD_LENGTH = 1024


def _prehash_password(password: str) -> bytes:
    """
    Pre-hash passwords using SHA-256 hex digest (64 ASCII bytes) to prevent
    bcrypt's silent 72-byte truncation vulnerability, ensuring distinct
    long passwords never authenticate equivalently.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")


def get_password_hash(password: str) -> str:
    """
    Generates a bcrypt hash of the SHA-256 pre-hashed password.
    Enforces a strict upper bound of 1024 characters to prevent CPU DoS.
    """
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password exceeds maximum allowed length of {MAX_PASSWORD_LENGTH} characters.")
    
    pwd_bytes = _prehash_password(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_and_check_rehash(plain_password: str, hashed_password: str) -> Tuple[bool, bool]:
    """
    Verifies a plain password against a stored bcrypt hash.
    
    Returns:
        (is_valid: bool, needs_rehash: bool)
    
    Security Policy:
    1. First validates against modern SHA-256 pre-hashed format (eliminates 72-byte truncation).
    2. Falls back to legacy raw bcrypt format for existing database records.
    3. Flags needs_rehash=True when authenticated via legacy hash so the caller
       can seamlessly re-hash to the modern format without disrupting existing users.
    """
    if not plain_password or not hashed_password or len(plain_password) > MAX_PASSWORD_LENGTH:
        return False, False

    try:
        h_bytes = hashed_password.encode("utf-8")
        
        # 1. Modern verification (SHA-256 pre-hashed)
        modern_digest = _prehash_password(plain_password)
        if bcrypt.checkpw(modern_digest, h_bytes):
            return True, False

        # 2. Backward-compatible legacy verification
        legacy_bytes = plain_password.encode("utf-8")[:72]
        if bcrypt.checkpw(legacy_bytes, h_bytes):
            return True, True

        return False, False
    except Exception:
        return False, False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Public helper matching standard FastAPI / auth interface."""
    is_valid, _ = verify_and_check_rehash(plain_password, hashed_password)
    return is_valid


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    except Exception:
        return None
