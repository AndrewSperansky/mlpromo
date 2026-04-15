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
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    username: Optional[str] = None
    password: str
    full_name: Optional[str] = None

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
        User.email == request.email,         # type: ignore
        User.is_deleted == False                        # type: ignore
    ).first()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Аккаунт не активирован. Ожидайте подтверждения администратором.")

    # Update last login

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    ActivityService.log(
        db=db,
        user_id=user.id,
        action="login",
        ip_address=req.client.host,
        user_agent=req.headers.get("user-agent")
    )

    # token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    token = create_access_token(data={"sub": str(user.id), "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
    }

# ==============================================
#  USER REGISTRATION
# ==============================================

@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # Проверяем email на уникальность
    existing = db.query(User).filter(
            User.email == request.email  # type: ignore
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    # Если username не указан, генерируем из email
    username = request.username or request.email.split('@')[0]

    user = User(
        username=username,
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        role=UserRole.ANALYST.value,  # ← analyst по умолчанию
        is_active=False  # ← новый пользователь неактивен
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Registration successful. Awaiting admin approval.", "user_id": user.id}

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


@router.delete("/users/{user_id}")
def delete_user(
        user_id: int,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first() # type: ignore
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    username = user.username
    user.is_deleted = True
    db.commit()

    # Логируем действие
    ActivityService.log(
        db=db,
        user_id=current_user.id,
        action="delete_user",
        resource=f"user_{user_id}",
        details=f"User {username} (id={user_id}) deleted by {current_user.username}"
    )

    return {"message": f"User {username} deleted"}



@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active
    }