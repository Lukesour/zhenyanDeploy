from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# 用户相关模型
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    target_score: Optional[float] = Field(None, ge=1.0, le=9.0)
    current_level: Optional[float] = Field(None, ge=1.0, le=9.0)
    exam_date: Optional[datetime] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    target_score: Optional[float] = Field(None, ge=1.0, le=9.0)
    current_level: Optional[float] = Field(None, ge=1.0, le=9.0)
    exam_date: Optional[datetime] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    target_score: Optional[float]
    current_level: Optional[float]
    exam_date: Optional[datetime]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# 作文相关模型
class TaskType(str, Enum):
    TASK1 = "task1"
    TASK2 = "task2"

class EssayType(str, Enum):
    AGREE_DISAGREE = "agree_disagree"
    DISCUSS_BOTH = "discuss_both"
    ADVANTAGES_DISADVANTAGES = "advantages_disadvantages"
    PROBLEM_SOLUTION = "problem_solution"
    TWO_PART_QUESTION = "two_part_question"

class EssaySubmit(BaseModel):
    task_type: TaskType
    essay_type: Optional[EssayType] = None
    title: str = Field(..., min_length=10)
    content: str = Field(..., min_length=100)
    # 可选：前端已调用 /chart/analyze 的结果，用于 Task1 评分联动
    chart_analysis: Optional[Dict[str, Any]] = None

class EssayResponse(BaseModel):
    id: int
    task_type: str
    essay_type: Optional[str]
    title: str
    content: str
    word_count: int
    is_graded: bool
    grading_status: str
    status: str
    created_at: datetime
    grading_result: Optional['GradingResultResponse'] = None
    # 提交后立即返回的“排队中”骨架（便于前端占位渲染）
    report_skeleton: Optional[Dict[str, Any]] = None

    @classmethod
    def model_validate(cls, obj):
        if hasattr(obj, '__dict__'):
            # 从ORM对象创建
            data = {}
            for field_name in cls.model_fields:
                if field_name == 'status':
                    # 将grading_status映射为status
                    data['status'] = getattr(obj, 'grading_status', 'pending')
                elif field_name == 'grading_status':
                    data['grading_status'] = getattr(obj, 'grading_status', data.get('status', 'pending'))
                elif field_name == 'is_graded':
                    data['is_graded'] = getattr(obj, 'is_graded', False)
                elif field_name == 'grading_result':
                    # 特殊处理grading_result字段
                    grading_result_obj = getattr(obj, field_name, None)
                    if grading_result_obj:
                        data[field_name] = GradingResultResponse.model_validate(grading_result_obj)
                    else:
                        data[field_name] = None
                elif hasattr(obj, field_name):
                    data[field_name] = getattr(obj, field_name)

            # 若处于 pending，则自动生成 report_skeleton
            try:
                if data.get('status') == 'pending':
                    prompt_analysis = getattr(obj, 'prompt_analysis', None)
                    data['report_skeleton'] = {
                        "summary": {
                            "overall_score": None,
                            "by_dimension": {"TR": None, "CC": None, "LR": None, "GRA": None}
                        },
                        "cards": [
                            {"dimension": d, "status": "queued", "score": None,
                             "evidence_items": [], "suggestion_items": [], "highlights": []}
                            for d in ["TR", "CC", "LR", "GRA"]
                        ],
                        "overall_comment": None,
                        "improvement_suggestions": [],
                        "prompt_analysis": prompt_analysis,
                    }
            except Exception:
                pass

            if 'grading_status' not in data:
                data['grading_status'] = data.get('status', 'pending')
            if 'is_graded' not in data:
                data['is_graded'] = getattr(obj, 'is_graded', False)

            return cls(**data)
        else:
            return super().model_validate(obj)

    class Config:
        from_attributes = True

# 评分相关模型
class DimensionAnalysis(BaseModel):
    score: float = Field(..., ge=1.0, le=9.0)
    strengths: List[str]
    weaknesses: List[str]
    evidence: List[str]
    suggestions: List[str]

class GradingResultResponse(BaseModel):
    id: int
    essay_id: int
    tr_score: float
    cc_score: float
    lr_score: float
    gra_score: float
    overall_score: float
    tr_analysis: Optional[Dict[str, Any]]
    cc_analysis: Optional[Dict[str, Any]]
    lr_analysis: Optional[Dict[str, Any]]
    gra_analysis: Optional[Dict[str, Any]]
    overall_comment: Optional[str]
    improvement_suggestions: Optional[List[str]]
    model_used: str
    processing_time: Optional[float]
    created_at: datetime
    #
    report: Optional[Dict[str, Any]] = None

    @classmethod
    def model_validate(cls, obj):
        if hasattr(obj, '__dict__'):
            # 从ORM对象创建
            data = {}
            for field_name in cls.model_fields:
                if field_name == 'improvement_suggestions':
                    # 处理improvement_suggestions字段的数据转换
                    raw_suggestions = getattr(obj, field_name, None)
                    if raw_suggestions:
                        if isinstance(raw_suggestions, list) and len(raw_suggestions) > 0:
                            # 检查是否为字典列表
                            if isinstance(raw_suggestions[0], dict):
                                # 从字典列表中提取description字段
                                data[field_name] = [
                                    suggestion.get('description', str(suggestion))
                                    for suggestion in raw_suggestions
                                ]
                            else:
                                # 已经是字符串列表
                                data[field_name] = raw_suggestions
                        else:
                            data[field_name] = []
                    else:
                        data[field_name] = []
                elif hasattr(obj, field_name):
                    data[field_name] = getattr(obj, field_name)

            # 组装前端卡片化结构（report）
            try:
                tr = getattr(obj, 'tr_analysis', None) or {}
                cc = getattr(obj, 'cc_analysis', None) or {}
                lr = getattr(obj, 'lr_analysis', None) or {}
                gra = getattr(obj, 'gra_analysis', None) or {}
                prompt_analysis = None
                # 若可访问到 essay 关系，带上 prompt_analysis（含 chart_analysis）
                essay_rel = getattr(obj, 'essay', None)
                if essay_rel is not None and hasattr(essay_rel, 'prompt_analysis'):
                    prompt_analysis = essay_rel.prompt_analysis

                def card(dim_name: str, score: float, analysis: Dict[str, Any]) -> Dict[str, Any]:
                    a = analysis if isinstance(analysis, dict) else {}
                    ev_items = a.get("evidence_items") or [
                        {"type": "text", "source": "rule", "weight": 1.0, "text": s, "spans": []}
                        for s in (a.get("evidence", []) or [])
                    ]
                    sug_items = a.get("suggestion_items") or [
                        {"type": "text", "source": "rule", "weight": 1.0, "text": s, "spans": []}
                        for s in (a.get("suggestions", []) or [])
                    ]
                    return {
                        "dimension": dim_name,
                        "score": score,
                        # Structured
                        "evidence_items": ev_items,
                        "suggestion_items": sug_items,
                        # backward compatible
                        "evidence": a.get("evidence", []),
                        "suggestions": a.get("suggestions", []),
                        "highlights": a.get("highlights", [])
                    }

                data['report'] = {
                    "summary": {
                        "overall_score": getattr(obj, 'overall_score', None),
                        "by_dimension": {
                            "TR": getattr(obj, 'tr_score', None),
                            "CC": getattr(obj, 'cc_score', None),
                            "LR": getattr(obj, 'lr_score', None),
                            "GRA": getattr(obj, 'gra_score', None)
                        }
                    },
                    "cards": [
                        card("TR", getattr(obj, 'tr_score', None), tr),
                        card("CC", getattr(obj, 'cc_score', None), cc),
                        card("LR", getattr(obj, 'lr_score', None), lr),
                        card("GRA", getattr(obj, 'gra_score', None), gra)
                    ],
                    "overall_comment": getattr(obj, 'overall_comment', None),
                    "improvement_suggestions": data.get('improvement_suggestions', []),
                    "prompt_analysis": prompt_analysis,
                }
            except Exception:
                # 容错：一旦构造report失败，不影响基本字段
                pass

            return cls(**data)
        else:
            return super().model_validate(obj)

    class Config:
        from_attributes = True


class EssaySubmitResponse(BaseModel):
    essay: EssayResponse
    remaining_analyses: int
    total_analyses_used: int

# 题目解析模型
class PromptAnalysis(BaseModel):
    essay_type: str
    key_instructions: List[str]
    question_points: List[str]
    required_elements: List[str]
    task_requirements: Dict[str, Any]

# 改进建议模型
class ImprovementSuggestion(BaseModel):
    category: str  # vocabulary, grammar, structure, content
    priority: str  # high, medium, low
    description: str
    specific_examples: List[str]
    replacement_suggestions: Optional[List[str]] = None

# API响应模型
class Token(BaseModel):
    access_token: str
    token_type: str

class Message(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
