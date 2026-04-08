# app/services/activity_service.py


from sqlalchemy.orm import Session
from app.models.user_activity import UserActivity
from typing import Optional

class ActivityService:
    @staticmethod
    def log_activity(
        db: Session,
        user_id: int,
        action: str,
        resource: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        activity = UserActivity(
            user_id=user_id,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(activity)
        db.commit()