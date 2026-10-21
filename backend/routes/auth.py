from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel

from backend.database import get_db
from backend.models.domain import User, AuditLog
from backend.security import get_password_hash, verify_password, create_access_token
from backend.dependencies import get_current_user, require_role
from backend.config import settings

router = APIRouter(tags=["auth"])

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str = None
    invitation_code: str = None

class UserProvisionRequest(BaseModel):
    email: str
    password: str
    full_name: str = None
    role: str = "RESEARCHER"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str = None
    role: str
    
    class Config:
        from_attributes = True

from backend.security import (
    get_password_hash, verify_password, verify_and_check_rehash,
    create_access_token, MAX_PASSWORD_LENGTH
)

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    clean_email = user_data.email.strip().lower() if user_data.email else ""
    if not clean_email or len(clean_email) > 255:
        raise HTTPException(status_code=400, detail="Invalid email address format.")

    # Phase 17: Enforce controlled pilot registration restrictions
    if settings.PILOT_REGISTRATION_RESTRICTED:
        valid_invitation = settings.PILOT_INVITATION_CODE
        provided_code = (user_data.invitation_code or "").strip()
        if not provided_code or provided_code != valid_invitation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Public self-registration is disabled for the controlled pilot. An authorized institutional invitation code is required."
            )

    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
    if len(user_data.password) > MAX_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password cannot exceed {MAX_PASSWORD_LENGTH} characters.")

    # Check if user exists
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=clean_email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name.strip() if user_data.full_name else None,
        role="RESEARCHER" # Hardcode to prevent admin escalation
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Audit Log
    db.add(AuditLog(user_id=new_user.id, action="USER_REGISTER", resource_type="User", resource_id=str(new_user.id)))
    db.commit()
    
    return new_user

@router.post("/admin/provision-user", response_model=UserResponse)
def provision_user_by_admin(
    provision_data: UserProvisionRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Administrator endpoint to provision authorized pilot participants.
    Strictly requires ADMIN role.
    """
    clean_email = provision_data.email.strip().lower() if provision_data.email else ""
    if not clean_email or len(clean_email) > 255:
        raise HTTPException(status_code=400, detail="Invalid email address format.")

    if len(provision_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
    if len(provision_data.password) > MAX_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password cannot exceed {MAX_PASSWORD_LENGTH} characters.")

    allowed_roles = ["ADMIN", "RESEARCHER", "VIEWER"]
    target_role = (provision_data.role or "RESEARCHER").upper()
    if target_role not in allowed_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role '{provision_data.role}'. Allowed: {allowed_roles}")

    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=clean_email,
        password_hash=get_password_hash(provision_data.password),
        full_name=provision_data.full_name.strip() if provision_data.full_name else None,
        role=target_role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    db.add(AuditLog(
        user_id=current_user.id,
        action="ADMIN_PROVISION_USER",
        resource_type="User",
        resource_id=str(new_user.id),
        metadata_info=f"Provisioned user {clean_email} with role {target_role}"
    ))
    db.commit()
    return new_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    if len(form_data.password) > MAX_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    clean_username = form_data.username.strip().lower() if form_data.username else ""
    user = db.query(User).filter(User.email == clean_username).first()
    
    if not user:
        # Constant-time mitigation against user enumeration
        _ = verify_password("dummy_constant_time_pass", "$2b$12$K1b9sK6iN1M4P1Q2A3B4C5D6E7F8G9H0I1J2K3L4M5N6O7P8Q9R0.")
        db.add(AuditLog(action="FAILED_LOGIN", resource_type="Auth", metadata_info=f"Attempt for email: {form_data.username}"))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    is_valid, needs_rehash = verify_and_check_rehash(form_data.password, user.password_hash)
    if not is_valid:
        db.add(AuditLog(action="FAILED_LOGIN", resource_type="Auth", metadata_info=f"Attempt for email: {form_data.username}"))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Seamless upgrade of legacy raw bcrypt hash to modern SHA-256 pre-hashed format
    if needs_rehash:
        user.password_hash = get_password_hash(form_data.password)
        
    user.last_login_at = datetime.now(timezone.utc)
    
    # Log successful login
    db.add(AuditLog(user_id=user.id, action="LOGIN", resource_type="Auth"))
    db.commit()

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
