import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import re

from backend.ielts.app.core.database import get_db
from backend.ielts.dependencies import get_ielts_user
from backend.ielts.app.models.user import User
from backend.ielts.app.models.essay import Essay, GradingResult
from backend.ielts.app.api.schemas import (
    EssaySubmit, 
    EssayResponse, 
    EssaySubmitResponse,
    GradingResultResponse,
    Message
)
from backend.ielts.app.services.grading_service import start_grading_task
from backend.api.auth import get_current_user, get_user_service
from backend.models.user_models import UserInfo
from backend.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/essays", tags=["IELTS Essays"])

def count_words(text: str) -> int:
    """统计单词数量"""
    # 移除多余的空白字符，按空格分割
    words = re.findall(r'\b\w+\b', text.lower())
    return len(words)

@router.post("/submit", response_model=EssaySubmitResponse)
async def submit_essay(
    essay_data: EssaySubmit,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_ielts_user),
    planner_user: UserInfo = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db),
    use_enhanced: bool = True
):
    """提交作文 - 支持增强评分模式"""
    # 统计字数
    word_count = count_words(essay_data.content)

    # 检查字数要求
    min_words = 150 if essay_data.task_type == "task1" else 250
    if word_count < min_words:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Essay must be at least {min_words} words. Current: {word_count} words."
        )

    if planner_user.remaining_analyses <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="分析次数已用完，请邀请好友获得更多机会"
        )

    try:
        await user_service.consume_analysis_chance(planner_user.id)
    except Exception as exc:
        message = str(exc) or "分析次数已用完，请邀请好友获得更多机会"
        logger.warning("Failed to consume shared usage for user %s: %s", planner_user.id, message)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )
    
    # 创建作文记录
    essay = Essay(
        user_id=current_user.id,
        task_type=essay_data.task_type.value,
        essay_type=essay_data.essay_type.value if essay_data.essay_type else None,
        title=essay_data.title,
        content=essay_data.content,
        word_count=word_count,
        grading_status="pending"
    )

    # 如提交时已携带图表分析，则预置到 prompt_analysis，供增强流程合并使用
    if getattr(essay_data, "chart_analysis", None):
        essay.prompt_analysis = {"chart_analysis": essay_data.chart_analysis}

    try:
        db.add(essay)
        db.commit()
        db.refresh(essay)
    except Exception as exc:
        db.rollback()
        logger.error("Failed to persist essay submission for user %s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="提交作文失败，请稍后重试"
        )

    updated_user = await user_service.get_user_info(planner_user.id)
    remaining = updated_user.remaining_analyses if updated_user else max(planner_user.remaining_analyses - 1, 0)
    total_used = updated_user.total_analyses_used if updated_user else planner_user.total_analyses_used + 1
    
    # 启动后台评分任务
    background_tasks.add_task(start_grading_task, essay.id, use_enhanced)
    
    return EssaySubmitResponse(
        essay=EssayResponse.model_validate(essay),
        remaining_analyses=remaining,
        total_analyses_used=total_used
    )

@router.get("/", response_model=List[EssayResponse])
def get_user_essays(
    current_user: User = Depends(get_ielts_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """获取用户的作文列表"""
    essays = db.query(Essay).filter(
        Essay.user_id == current_user.id
    ).order_by(Essay.created_at.desc()).offset(skip).limit(limit).all()
    
    return [EssayResponse.model_validate(essay) for essay in essays]

@router.get("/{essay_id}", response_model=EssayResponse)
def get_essay(
    essay_id: int,
    current_user: User = Depends(get_ielts_user),
    db: Session = Depends(get_db)
):
    """获取特定作文"""
    from sqlalchemy.orm import joinedload

    essay = db.query(Essay).options(
        joinedload(Essay.grading_result)
    ).filter(
        Essay.id == essay_id,
        Essay.user_id == current_user.id
    ).first()

    if not essay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Essay not found"
        )

    return EssayResponse.model_validate(essay)

@router.get("/{essay_id}/result", response_model=GradingResultResponse)
def get_grading_result(
    essay_id: int,
    current_user: User = Depends(get_ielts_user),
    db: Session = Depends(get_db)
):
    """获取作文评分结果"""
    essay = db.query(Essay).filter(
        Essay.id == essay_id,
        Essay.user_id == current_user.id
    ).first()
    
    if not essay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Essay not found"
        )
    
    if not essay.is_graded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Essay grading is {essay.grading_status}"
        )
    
    result = db.query(GradingResult).filter(
        GradingResult.essay_id == essay_id
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grading result not found"
        )
    
    return result

@router.delete("/{essay_id}", response_model=Message)
def delete_essay(
    essay_id: int,
    current_user: User = Depends(get_ielts_user),
    db: Session = Depends(get_db)
):
    """删除作文"""
    essay = db.query(Essay).filter(
        Essay.id == essay_id,
        Essay.user_id == current_user.id
    ).first()
    
    if not essay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Essay not found"
        )
    
    db.delete(essay)
    db.commit()
    
    return {"message": "Essay deleted successfully"}
