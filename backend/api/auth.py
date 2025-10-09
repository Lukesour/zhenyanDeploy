from fastapi import APIRouter, HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from backend.models.user_models import (
    UserRegisterRequest, UserLoginRequest, SendVerificationCodeRequest,
    UseInvitationRequest, UserInfo, LoginResponse, UserProfileData
)
from backend.services.user_service import UserService

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# HTTP Bearer token scheme
security = HTTPBearer()

# 全局用户服务实例
user_service = None

def get_user_service() -> UserService:
    """获取用户服务实例"""
    global user_service
    if user_service is None:
        user_service = UserService()
    return user_service

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: UserService = Depends(get_user_service)
) -> UserInfo:
    """获取当前登录用户"""
    try:
        token = credentials.credentials
        user_id = service.verify_jwt_token(token)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的访问令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_info = await service.get_user_info(user_id)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="身份验证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )



@router.post("/send-verification-code")
async def send_verification_code(
    request: SendVerificationCodeRequest,
    service: UserService = Depends(get_user_service)
):
    """发送邮箱验证码"""
    try:
        success = await service.send_verification_code(request.email, request.phone)

        if success:
            return {
                "success": True,
                "message": "验证码已发送到您的邮箱，请查收",
                "expires_in": 600  # 10分钟
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="验证码发送失败，请稍后重试"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送验证码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/register", response_model=LoginResponse)
async def register_user(
    request: UserRegisterRequest,
    service: UserService = Depends(get_user_service)
):
    """用户注册"""
    try:
        # 注册用户
        user_info = await service.register_user(
            request.phone,
            request.email,
            request.verification_code,
            request.invitation_code,
            request.profile_data
        )
        
        # 生成登录令牌
        token_data = service.generate_jwt_token(user_info.id)
        
        return LoginResponse(
            access_token=token_data['access_token'],
            token_type=token_data['token_type'],
            expires_in=token_data['expires_in'],
            user_info=user_info
        )
        
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: UserLoginRequest,
    service: UserService = Depends(get_user_service)
):
    """用户登录"""
    try:
        login_data = await service.login_user(request.phone, request.email, request.verification_code, request.profile_data)
        
        return LoginResponse(
            access_token=login_data['access_token'],
            token_type=login_data['token_type'],
            expires_in=login_data['expires_in'],
            user_info=login_data['user_info'],
            is_new_user=login_data.get('is_new_user', False)
        )
        
    except Exception as e:
        logger.error(f"用户登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/debug/verification-code/{email}/{phone}")
async def get_cached_verification_code(
    email: str,
    phone: str,
    service: UserService = Depends(get_user_service)
):
    """获取缓存的验证码（仅用于调试）"""
    try:
        code = service.get_cached_verification_code(email, phone)
        if code:
            return {
                "success": True,
                "verification_code": code,
                "message": "验证码获取成功"
            }
        else:
            return {
                "success": False,
                "message": "未找到有效的验证码"
            }
    except Exception as e:
        logger.error(f"获取验证码失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user-info", response_model=UserInfo)
async def get_user_info(
    current_user: UserInfo = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user

@router.post("/refresh-token")
async def refresh_token(
    current_user: UserInfo = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """刷新访问令牌"""
    try:
        token_data = service.generate_jwt_token(current_user.id)
        
        return {
            "access_token": token_data['access_token'],
            "token_type": token_data['token_type'],
            "expires_in": token_data['expires_in']
        }
        
    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败"
        )

@router.post("/profile", response_model=UserInfo)
async def update_user_profile(
    profile_data: UserProfileData,
    current_user: UserInfo = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """保存或更新用户个人信息"""
    try:
        saved = await service.save_user_profile(current_user.id, profile_data)
        if not saved:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="保存用户个人信息失败"
            )

        updated_user = await service.get_user_info(current_user.id)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存用户个人信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="保存用户个人信息失败"
        )

@router.post("/logout")
async def logout_user(
    authorization: Optional[str] = Header(None),
    service: UserService = Depends(get_user_service)
):
    """用户退出登录"""
    try:
        # 如果提供了Authorization头，验证token并记录用户信息
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
            user_id = service.verify_jwt_token(token)

            if user_id:
                try:
                    user_info = await service.get_user_info(user_id)
                    if user_info:
                        logger.info(f"用户 {user_info.id} ({user_info.phone}) 退出登录")
                    else:
                        logger.info(f"用户ID {user_id} 退出登录（用户信息未找到）")
                except Exception as e:
                    logger.warning(f"获取用户信息失败，但继续退出登录: {str(e)}")
                    logger.info(f"用户ID {user_id} 退出登录")
            else:
                logger.info("无效token的退出登录请求")
        else:
            logger.info("无token的退出登录请求")

        # 无论如何都返回成功，让前端清除本地状态
        return {
            "success": True,
            "message": "退出登录成功"
        }

    except Exception as e:
        logger.error(f"退出登录处理失败: {str(e)}")
        # 即使出错也返回成功，确保前端能够清除状态
        return {
            "success": True,
            "message": "退出登录成功"
        }

@router.get("/get-verification-code")
async def get_verification_code(
    email: str,
    phone: str,
    service: UserService = Depends(get_user_service)
):
    """获取验证码（仅用于测试）"""
    try:
        # 仅在调试模式下提供此功能
        from backend.config.settings import settings
        if not settings.DEBUG:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not found"
            )

        code = await service.get_verification_code(email, phone)
        if code:
            return {"code": code}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="验证码不存在或已过期"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取验证码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/use-invitation")
async def use_invitation_code(
    request: UseInvitationRequest,
    current_user: UserInfo = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """使用邀请码（已注册用户也可以使用）"""
    try:
        # 这里可以实现已注册用户使用邀请码的逻辑
        # 暂时返回提示信息
        return {
            "success": False,
            "message": "邀请码功能仅在注册时可用"
        }

    except Exception as e:
        logger.error(f"使用邀请码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/invitation-info")
async def get_invitation_info(
    current_user: UserInfo = Depends(get_current_user)
):
    """获取用户的邀请码信息"""
    try:
        return {
            "invitation_code": current_user.invitation_code,
            "invited_count": current_user.invited_count,
            "reward_per_invitation": 3,
            "total_rewards": current_user.invited_count * 3
        }
        
    except Exception as e:
        logger.error(f"获取邀请信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取邀请信息失败"
        )

@router.get("/analysis-stats")
async def get_analysis_stats(
    current_user: UserInfo = Depends(get_current_user)
):
    """获取用户分析统计信息"""
    try:
        return {
            "remaining_analyses": current_user.remaining_analyses,
            "total_analyses_used": current_user.total_analyses_used,
            "invited_count": current_user.invited_count,
            "total_earned_analyses": current_user.invited_count * 3
        }
        
    except Exception as e:
        logger.error(f"获取分析统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取分析统计失败"
        )

@router.get("/health")
async def health_check(
    service: UserService = Depends(get_user_service)
):
    """健康检查"""
    try:
        db_ok = service.test_connection()
        email_ok = service.email_service.test_connection()
        email_verification_ok = await service.test_email_verification_service()

        overall_healthy = db_ok and email_ok and email_verification_ok

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "database": "ok" if db_ok else "error",
            "email_service": "ok" if email_ok else "error",
            "email_verification": "ok" if email_verification_ok else "error"
        }

    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
