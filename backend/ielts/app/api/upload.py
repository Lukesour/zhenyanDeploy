"""
文件上传API
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from ..services.ocr_service import ocr_service
from ..services.chart_analysis_service import chart_analysis_service
from backend.ielts.dependencies import get_ielts_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/upload", tags=["IELTS Upload"])

# 支持的图片格式和最大文件大小
SUPPORTED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png", 
    "image/bmp", "image/tiff", "image/webp"
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/ocr/extract-text")
async def extract_text_from_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_ielts_user)
) -> Dict[str, Any]:
    """
    从上传的图片中提取文字
    """
    try:
        # 验证文件类型
        if file.content_type not in SUPPORTED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}。支持的格式: {', '.join(SUPPORTED_IMAGE_TYPES)}"
            )
        
        # 读取文件内容
        file_content = await file.read()
        
        # 验证文件大小
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大。最大支持 {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # 验证文件不为空
        if len(file_content) == 0:
            raise HTTPException(
                status_code=400,
                detail="上传的文件为空"
            )
        
        # 执行OCR
        result = ocr_service.extract_text_from_image(
            image_data=file_content,
            filename=file.filename or ""
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "OCR处理失败")
            )
        
        logger.info(f"用户 {current_user.email} 成功提取图片文字，置信度: {result['confidence']}%")
        
        return {
            "success": True,
            "data": {
                "text": result["text"],
                "confidence": result["confidence"],
                "word_count": result["word_count"],
                "char_count": result["char_count"]
            },
            "message": "文字提取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR处理异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )


@router.post("/ocr/extract-title")
async def extract_title_from_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_ielts_user)
) -> Dict[str, Any]:
    """
    从上传的图片中仅提取题目
    """
    try:
        # 验证文件类型
        if file.content_type not in SUPPORTED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}。支持的格式: {', '.join(SUPPORTED_IMAGE_TYPES)}"
            )

        # 读取文件内容
        file_content = await file.read()

        # 验证文件大小
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大。最大支持 {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # 验证文件不为空
        if len(file_content) == 0:
            raise HTTPException(
                status_code=400,
                detail="上传的文件为空"
            )

        # 执行OCR提取题目
        result = ocr_service.extract_title_only(
            image_data=file_content,
            filename=file.filename or ""
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "题目提取失败")
            )

        logger.info(f"用户 {current_user.email} 成功提取题目，置信度: {result['confidence']}%")

        return {
            "success": True,
            "data": {
                "title": result["title"],
                "confidence": result["confidence"],
                "word_count": result["word_count"]
            },
            "message": "题目提取成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"题目OCR处理异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )

@router.post("/ocr/extract-content")
async def extract_content_from_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_ielts_user)
) -> Dict[str, Any]:
    """
    从上传的图片中仅提取作文内容
    """
    try:
        # 验证文件类型
        if file.content_type not in SUPPORTED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}。支持的格式: {', '.join(SUPPORTED_IMAGE_TYPES)}"
            )

        # 读取文件内容
        file_content = await file.read()

        # 验证文件大小
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大。最大支持 {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # 验证文件不为空
        if len(file_content) == 0:
            raise HTTPException(
                status_code=400,
                detail="上传的文件为空"
            )

        # 执行OCR提取内容
        result = ocr_service.extract_content_only(
            image_data=file_content,
            filename=file.filename or ""
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "内容提取失败")
            )

        logger.info(f"用户 {current_user.email} 成功提取作文内容，置信度: {result['confidence']}%")

        return {
            "success": True,
            "data": {
                "content": result["content"],
                "confidence": result["confidence"],
                "word_count": result["word_count"]
            },
            "message": "作文内容提取成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"内容OCR处理异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )

@router.post("/chart/analyze")
async def analyze_chart_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_ielts_user)
) -> Dict[str, Any]:
    """
    分析Task1图表、流程图等图片
    """
    try:
        # 验证文件类型
        if file.content_type not in SUPPORTED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}。支持的格式: {', '.join(SUPPORTED_IMAGE_TYPES)}"
            )

        # 读取文件内容
        file_content = await file.read()

        # 验证文件大小
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大。最大支持 {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # 验证文件不为空
        if len(file_content) == 0:
            raise HTTPException(
                status_code=400,
                detail="上传的文件为空"
            )

        # 执行图表分析
        result = await chart_analysis_service.analyze_chart(
            image_data=file_content,
            filename=file.filename or ""
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "图表分析失败")
            )

        logger.info(f"用户 {current_user.email} 成功分析图表，类型: {result['chart_type']}")

        return {
            "success": True,
            "data": {
                "chart_type": result["chart_type"],
                "description": result["description"],
                "temporal_dimension": result.get("temporal_dimension"),
                "axes": result.get("axes"),
                "categories": result.get("categories"),
                "key_features": result["key_features"],
                "data_points": result["data_points"],
                "trends": result["trends"],
                "tense_recommendation": result.get("tense_recommendation"),
                "writing_suggestions": result["writing_suggestions"]
            },
            "message": "图表分析成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图表分析异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误，请稍后重试"
        )

@router.get("/ocr/info")
async def get_ocr_info() -> Dict[str, Any]:
    """
    获取OCR服务信息
    """
    return {
        "success": True,
        "data": {
            "supported_formats": list(SUPPORTED_IMAGE_TYPES),
            "max_file_size_mb": MAX_FILE_SIZE // (1024*1024),
            "features": [
                "中英文混合识别",
                "分别提取题目和内容",
                "Task1图表分析",
                "图片预处理优化",
                "置信度评估"
            ]
        },
        "message": "OCR服务信息"
    }
