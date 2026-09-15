from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel

from backend.database import get_db
from backend.models.domain import User, AuditLog
from backend.security import get_password_hash, verify_password, create_access_token
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str = None
    role: str
    
    class Config:
        from_attributes = True

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role="RESEARCHER" # Hardcode to prevent admin escalation
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Audit Log
    db.add(AuditLog(user_id=new_user.id, action="USER_REGISTER", resource_type="User", resource_id=str(new_user.id)))
    db.commit()
    
    return new_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        # Log failed attempt without revealing if user exists
        db.add(AuditLog(action="FAILED_LOGIN", resource_type="Auth", metadata_info=f"Attempt for email: {form_data.username}"))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    user.last_login_at = datetime.now(timezone.utc)
    
    # Log successful login
    db.add(AuditLog(user_id=user.id, action="LOGIN", resource_type="Auth"))
    db.commit()

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
