"""
超详细改进建议API端点
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

from backend.ielts.app.services.ultra_detailed_improvement_service import ultra_detailed_improvement_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ultra-improvements", tags=["IELTS Improvements"])

class ImprovementRequest(BaseModel):
    """改进建议请求模型"""
    essay_content: str = Field(..., description="作文内容")
    essay_title: str = Field(..., description="作文题目")
    dimension_scores: Dict[str, float] = Field(..., description="各维度分数")
    overall_score: float = Field(..., description="总分")
    target_score: Optional[float] = Field(None, description="目标分数")
    analysis_type: str = Field("complete", description="分析类型")

class ImprovementResponse(BaseModel):
    """改进建议响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    analysis_type: str
    essay_title: str

@router.post("/generate", response_model=ImprovementResponse)
async def generate_ultra_detailed_improvements(request: ImprovementRequest):
    """
    生成超详细的改进建议
    
    支持的分析类型：
    - complete: 完整改进建议包（推荐）
    - comprehensive: 综合详细改进建议
    - sentence: 逐句详细分析
    - error: 全面错误分析
    - comparison: 范文对比分析
    - learning: 个性化学习计划
    """
    
    try:
        logger.info(f"Received improvement request for essay: {request.essay_title}")
        
        # 验证分析类型
        available_types = ultra_detailed_improvement_service.get_available_analysis_types()
        if request.analysis_type not in available_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis type. Available types: {list(available_types.keys())}"
            )
        
        # 验证分数范围
        if not (0 <= request.overall_score <= 9):
            raise HTTPException(
                status_code=400,
                detail="Overall score must be between 0 and 9"
            )
        
        for dim, score in request.dimension_scores.items():
            if not (0 <= score <= 9):
                raise HTTPException(
                    status_code=400,
                    detail=f"Dimension score for {dim} must be between 0 and 9"
                )
        
        # 生成改进建议
        result = await ultra_detailed_improvement_service.generate_complete_improvement_analysis(
            essay_content=request.essay_content,
            essay_title=request.essay_title,
            dimension_scores=request.dimension_scores,
            overall_score=request.overall_score,
            target_score=request.target_score,
            analysis_type=request.analysis_type
        )
        
        if result.get("success", True):
            return ImprovementResponse(
                success=True,
                data=result,
                analysis_type=request.analysis_type,
                essay_title=request.essay_title
            )
        else:
            return ImprovementResponse(
                success=False,
                error=result.get("error", "Unknown error occurred"),
                analysis_type=request.analysis_type,
                essay_title=request.essay_title
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating improvements: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/analysis-types")
async def get_analysis_types():
    """获取可用的分析类型"""
    try:
        types = ultra_detailed_improvement_service.get_available_analysis_types()
        return {
            "success": True,
            "analysis_types": types
        }
    except Exception as e:
        logger.error(f"Error getting analysis types: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/summary")
async def generate_improvement_summary(request: ImprovementRequest):
    """生成改进建议摘要"""
    try:
        result = await ultra_detailed_improvement_service.generate_improvement_summary(
            essay_content=request.essay_content,
            essay_title=request.essay_title,
            dimension_scores=request.dimension_scores,
            overall_score=request.overall_score
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating improvement summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/data-resources")
async def get_data_resources_info():
    """获取数据资源信息"""
    try:
        info = ultra_detailed_improvement_service.get_data_resources_info()
        return {
            "success": True,
            "data": info
        }
    except Exception as e:
        logger.error(f"Error getting data resources info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/quick-analysis")
async def quick_improvement_analysis(request: ImprovementRequest):
    """快速改进分析 - 适合实时反馈"""
    try:
        # 使用综合分析类型进行快速分析
        result = await ultra_detailed_improvement_service.generate_complete_improvement_analysis(
            essay_content=request.essay_content,
            essay_title=request.essay_title,
            dimension_scores=request.dimension_scores,
            overall_score=request.overall_score,
            target_score=request.target_score,
            analysis_type="comprehensive"  # 使用综合分析而不是完整包
        )
        
        return {
            "success": True,
            "data": result,
            "analysis_type": "comprehensive",
            "note": "This is a quick analysis. For complete analysis, use the /generate endpoint with analysis_type='complete'"
        }
        
    except Exception as e:
        logger.error(f"Error in quick analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
