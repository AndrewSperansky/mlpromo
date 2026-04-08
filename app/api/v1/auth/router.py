# app/api/v1/auth/router.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from datetime import datetime, timezone
from app.models.user import User, UserRole
from app.auth.jwt import create_access_token, verify_password, get_password_hash
from app.auth.dependencies import get_current_user, require_admin
from app.models.user_activity import UserActivity
from app.services.activity_service import ActivityService

router = APIRouter(tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str = None

class UserUpdateRequest(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: str

# ==============================================
#  USER LOGIN
# ==============================================


@router.post("/login")
def login(request: LoginRequest, req: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == request.username,    # type: ignore
        User.is_deleted == False                        # type: ignore
    ).first()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account disabled")

    # Update last login

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    ActivityService.log_activity(
        db=db,
        user_id=user.id,
        action="login",
        ip_address=req.client.host,
        user_agent=req.headers.get("user-agent")
    )

    # token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    token = create_access_token(data={"sub": str(user.id), "role": user.role})

    return {"access_token": token, "token_type": "bearer", "user": {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name
    }}

# ==============================================
#  USER REGISTRATION
# ==============================================

@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        or_(
            User.username == request.username,  # type: ignore
            User.email == request.email  # type: ignore
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    user = User(
        username=request.username,
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        role="viewer",
        is_active=False  # ← новый пользователь неактивен
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created successfully. Awaiting admin approval.", "user_id": user.id}

# ==============================================
#  USER LOGOUT
# ==============================================

@router.post("/logout")
def logout():
    # JWT без сохранения на сервере — просто возвращаем успех
    return {"message": "Logged out successfully"}


@router.get("/activities")
def get_activities(
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        _current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    query = db.query(UserActivity)

    if user_id:
        query = query.filter(UserActivity.user_id == user_id)   # type: ignore
    if action:
        query = query.filter(UserActivity.action == action)     # type: ignore
    if date_from:
        query = query.filter(UserActivity.created_at >= date_from)
    if date_to:
        query = query.filter(UserActivity.created_at <= date_to)

    activities = query.order_by(UserActivity.created_at.desc()).offset(skip).limit(limit).all()

    # Join with users to get username and role
    result = []
    for act in activities:
        user = db.query(User).filter(User.id == act.user_id).first()    # type: ignore
        result.append({
            "id": act.id,
            "user_id": act.user_id,
            "username": user.username if user else "deleted",
            "user_role": user.role if user else "unknown",
            "action": act.action,
            "resource": act.resource,
            "details": act.details,
            "ip_address": act.ip_address,
            "created_at": act.created_at.isoformat()
        })

    return result

# ==============================================
#  USERS LIST
# ==============================================

@router.get("/users")
def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).filter(User.is_deleted.is_(False)).offset(skip).limit(limit).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None
        }
        for u in users
    ]

# ==============================================
#  USER BLOCK
# ==============================================

@router.post("/users/{user_id}/block")
def block_user(
        user_id: int,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")

    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()  # type: ignore
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()

    return {"message": f"User {user.username} blocked"}

# ==============================================
#  USER UNBLOCK
# ==============================================

@router.post("/users/{user_id}/unblock")
def unblock_user(
        user_id: int,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()  # type: ignore
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.commit()

    return {"message": f"User {user.username} unblocked"}



# ==============================================
#  USER UPDATE
# ==============================================

@router.put("/users/{user_id}")
def update_user(
        user_id: int,
        request: UserUpdateRequest,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()  # type: ignore
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email = request.email
    user.full_name = request.full_name
    user.role = request.role
    db.commit()

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name,
        "is_active": user.is_active
    }