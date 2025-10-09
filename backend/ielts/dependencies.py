from fastapi import Depends
from sqlalchemy.orm import Session
import secrets
from datetime import datetime

from backend.api.auth import get_current_user
from backend.ielts.app.core.database import get_db
from backend.ielts.app.models.user import User as IELTSUser
from backend.models.user_models import UserInfo

PLACEHOLDER_PASSWORD_PREFIX = "planner_managed_"


def _ensure_username(email: str | None, phone: str | None, user_id: int) -> str:
    if email:
        return email.split("@")[0]
    if phone:
        return f"user_{phone[-4:]}"
    return f"user_{user_id}"

def _parse_exam_date(value):
    if value in (None, '', 'null'):
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except Exception:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except Exception:
            return None

def get_ielts_user(
    planner_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IELTSUser:
    """Map the authenticated planner user to an IELTS user record."""
    user = db.query(IELTSUser).filter(IELTSUser.id == planner_user.id).first()
    profile = planner_user.profile_data.dict() if getattr(planner_user, 'profile_data', None) else {}
    if user:
        updated = False
        if planner_user.email and user.email != planner_user.email:
            user.email = planner_user.email
            updated = True
        target_score = profile.get('language_target_total_score')
        if target_score is None:
            target_score = profile.get('target_score')
        if target_score is not None and user.target_score != target_score:
            user.target_score = float(target_score)
            updated = True
        current_level = profile.get('language_total_score')
        if current_level is None:
            current_level = profile.get('current_level')
        if current_level is not None and user.current_level != current_level:
            user.current_level = float(current_level)
            updated = True
        exam_date_value = profile.get('language_expected_test_date')
        if exam_date_value is None:
            exam_date_value = profile.get('exam_date')
        if exam_date_value is None and user.exam_date is not None:
            user.exam_date = None
            updated = True
        else:
            parsed_exam_date = _parse_exam_date(exam_date_value)
            if parsed_exam_date and user.exam_date != parsed_exam_date:
                user.exam_date = parsed_exam_date
                updated = True
        if updated:
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    placeholder_password = PLACEHOLDER_PASSWORD_PREFIX + secrets.token_hex(16)
    username = _ensure_username(planner_user.email, planner_user.phone, planner_user.id)
    target_score = profile.get('language_target_total_score')
    if target_score is None:
        target_score = profile.get('target_score')
    current_level = profile.get('language_total_score')
    if current_level is None:
        current_level = profile.get('current_level')
    try:
        target_score = float(target_score) if target_score is not None else None
    except (TypeError, ValueError):
        target_score = None
    try:
        current_level = float(current_level) if current_level is not None else None
    except (TypeError, ValueError):
        current_level = None
    exam_date_value = profile.get('language_expected_test_date')
    if exam_date_value is None:
        exam_date_value = profile.get('exam_date')
    parsed_exam_date = _parse_exam_date(exam_date_value)

    user = IELTSUser(
        id=planner_user.id,
        email=planner_user.email or f"user{planner_user.id}@example.com",
        username=username,
        hashed_password=placeholder_password,
        target_score=target_score,
        current_level=current_level,
        exam_date=parsed_exam_date,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
