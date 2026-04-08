from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.session import get_db
from app.models.user import User, UserRole
from app.auth.jwt import decode_token

security = HTTPBearer()


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Исправлено: используем and_ с правильными операторами
    user = db.query(User).filter(
        and_(
            User.id == int(user_id),
            User.is_active == True,  # type: ignore
            User.is_deleted == False  # type: ignore
        )
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user   # type: ignore


def require_role(roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {roles}, your role: {current_user.role}"
            )
        return current_user
    return role_checker

# Готовые зависимости
require_admin = require_role(["admin"])
require_ml_engineer = require_role(["admin", "ml_engineer"])
require_analyst = require_role(["admin", "ml_engineer", "analyst"])
require_authenticated = get_current_user