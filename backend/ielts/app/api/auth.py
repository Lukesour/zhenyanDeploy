from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.ielts.dependencies import get_ielts_user
from backend.ielts.app.core.database import get_db
from backend.ielts.app.models.user import User as IELTSUser
from backend.ielts.app.api.schemas import UserResponse, UserProfile, Token

router = APIRouter(prefix="/api/v1/auth", tags=["IELTS Auth Compatibility"])


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: IELTSUser = Depends(get_ielts_user)):
    """Return IELTS-compatible user payload for the authenticated planner user."""
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_data: UserProfile,
    current_user: IELTSUser = Depends(get_ielts_user),
    db: Session = Depends(get_db),
):
    """Update IELTS user profile information while syncing planner-authenticated account."""
    if profile_data.target_score is not None:
        current_user.target_score = profile_data.target_score
    if profile_data.current_level is not None:
        current_user.current_level = profile_data.current_level
    if profile_data.exam_date is not None:
        current_user.exam_date = profile_data.exam_date

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/register", response_model=Token)
def legacy_register_not_supported():
    """Legacy password-based registration is disabled in favour of unified planner auth."""
    raise HTTPException(
        status_code=400,
        detail="请通过 /api/auth/register 完成验证登录流程",
    )


@router.post("/login", response_model=Token)
def legacy_login_not_supported():
    """Legacy password-based login is disabled in favour of unified planner auth."""
    raise HTTPException(
        status_code=400,
        detail="请使用邮箱验证码登录流程：/api/auth/login",
    )
