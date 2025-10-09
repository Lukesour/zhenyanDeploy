"""
评语格式化API端点
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging

from backend.ielts.app.services.comment_formatter import comment_formatter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/comment-formatter", tags=["IELTS Comments"])

class FormatCommentRequest(BaseModel):
    """格式化评语请求模型"""
    raw_comment: str
    comment_type: str = "overall"  # overall, improvement, dimension

class FormatCommentResponse(BaseModel):
    """格式化评语响应模型"""
    success: bool
    formatted_comment: str
    is_formatted: bool
    original_format: str
    sections: Dict[str, Any] = None
    error: str = None

@router.post("/format-comment", response_model=FormatCommentResponse)
async def format_comment(request: FormatCommentRequest):
    """
    格式化评语 - 将JSON格式的评语转换为用户友好的显示格式
    """
    
    try:
        logger.info(f"Formatting comment of type: {request.comment_type}")
        
        if request.comment_type == "overall":
            # 格式化总体评语
            result = comment_formatter.parse_and_format_comment(request.raw_comment)
        elif request.comment_type == "improvement":
            # 格式化改进建议
            result = comment_formatter.format_improvement_suggestions(request.raw_comment)
        else:
            # 默认处理
            result = comment_formatter.parse_and_format_comment(request.raw_comment)
        
        return FormatCommentResponse(
            success=True,
            formatted_comment=result.get("formatted_comment", ""),
            is_formatted=result.get("is_formatted", False),
            original_format=result.get("original_format", "unknown"),
            sections=result.get("sections"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error formatting comment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/test-format")
async def test_format_comment():
    """
    测试评语格式化功能
    """
    
    # 测试用的JSON格式评语
    test_comment = '''
    {
        "overall_comment": "总的来说，您的作文基本完成了任务要求，清晰地表达了您对"公司和个人应该为污染清理买单"这一观点的赞同。文章结构完整，包含引言、主体段落和结论。然而，在论证深度、语言准确性和逻辑连贯性方面仍有提升空间。",
        "score_breakdown": {
            "TR_analysis": "任务回应维度（Task Response）得分6.5分。您明确表达了立场，并尝试提出了多个论点来支持观点。然而，论证深度不足，缺乏具体、有力的证据支持。",
            "CC_analysis": "连贯与衔接维度（Coherence and Cohesion）得分6.0分。文章结构基本清晰，尝试使用分段来组织论点。但衔接词使用较为机械。",
            "LR_analysis": "词汇资源维度（Lexical Resource）得分6.0分。您能够使用足够词汇完成写作任务，但词汇选择较为有限，缺乏多样性。",
            "GRA_analysis": "语法准确性维度（Grammatical Range and Accuracy）得分6.0分。您尝试使用复杂句式，但语法错误较多，影响了阅读流畅性。"
        },
        "key_strengths": [
            "清晰表达了对题目的立场",
            "文章结构完整，包含引言、主体段落和结论",
            "尝试提出了多个论点来支持观点"
        ],
        "key_weaknesses": [
            "论证深度不足，缺乏具体证据支撑",
            "语言表达不够准确，存在语法和拼写错误",
            "逻辑连贯性较弱，衔接词使用不够自然"
        ],
        "priority_improvements": [
            "加强论证的深度和广度，提供更具体、更有说服力的证据来支持你的观点",
            "注重语言的准确性和多样性，避免重复使用简单词汇",
            "提升逻辑思维能力，使文章的论证更加清晰、连贯"
        ],
        "score_justification": "综合考虑以上各维度，您的作文表现达到Band 6的水平。虽然您能够完成任务要求，但论证深度、语言准确性和逻辑连贯性方面仍有提升空间。因此，最终评分为6.0分。",
        "band_level_description": "Band 6的作文能够回应题目要求，观点明确，但论证不够充分，语言表达不够准确，逻辑连贯性较弱。",
        "next_level_requirements": "要达到Band 7，您需要加强论证的深度和广度，提供更具体、更有说服力的证据来支持你的观点。",
        "official_standards_alignment": "您的作文符合Band 6的官方评分标准，即"回应了问题的主要部分，提出了一个切题的观点，多个主要论点与问题相关，但某些论点未能充分进行论证或不甚清晰。""
    }
    '''
    
    try:
        # 格式化测试评语
        result = comment_formatter.parse_and_format_comment(test_comment)
        
        return {
            "success": True,
            "message": "测试格式化成功",
            "original_length": len(test_comment),
            "formatted_length": len(result.get("formatted_comment", "")),
            "is_formatted": result.get("is_formatted", False),
            "formatted_preview": result.get("formatted_comment", "")[:500] + "..." if len(result.get("formatted_comment", "")) > 500 else result.get("formatted_comment", ""),
            "sections_count": len(result.get("sections", {}))
        }
        
    except Exception as e:
        logger.error(f"Error in test format: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Test failed: {str(e)}"
        )

@router.get("/format-demo")
async def format_demo():
    """
    演示评语格式化效果
    """
    
    # 原始JSON格式
    raw_json = '''{"overall_comment": "总的来说，您的作文基本完成了任务要求。", "key_strengths": ["清晰表达了立场", "结构完整"], "key_weaknesses": ["论证深度不足", "语法错误较多"], "priority_improvements": ["加强论证深度", "提高语言准确性"]}'''
    
    # 格式化后的效果
    formatted_result = comment_formatter.parse_and_format_comment(raw_json)
    
    return {
        "demo_title": "评语格式化演示",
        "before": {
            "title": "格式化前（JSON格式）",
            "content": raw_json
        },
        "after": {
            "title": "格式化后（用户友好格式）",
            "content": formatted_result.get("formatted_comment", "")
        },
        "improvement": {
            "readability": "大幅提升",
            "structure": "清晰的章节划分",
            "user_experience": "更加友好"
        }
    }
