from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Pydantic Models for API
class UserBackground(BaseModel):
    # Academic background
    undergraduate_university: str
    undergraduate_major: str
    gpa: float
    gpa_scale: str  # "4.0" or "100"
    graduation_year: int

    # Language scores (required)
    language_test_status: str = "未报考并且不准备考"  # "已考试", "未报考、准备考", "准备再考", "未报考并且不准备考"
    language_test_type: Optional[str] = None  # "TOEFL" or "IELTS"
    language_total_score: Optional[float] = None
    language_reading: Optional[float] = None
    language_listening: Optional[float] = None
    language_speaking: Optional[float] = None
    language_writing: Optional[float] = None
    # Target scores for language tests
    language_target_total_score: Optional[float] = None
    language_target_reading: Optional[float] = None
    language_target_listening: Optional[float] = None
    language_target_speaking: Optional[float] = None
    language_target_writing: Optional[float] = None
    # Expected test date for language tests
    language_expected_test_date: Optional[str] = None  # 预期考试时间

    # Standardized test scores (optional)
    gre_test_status: Optional[str] = "未报考并且不准备考"  # "已考试", "未报考、准备考", "准备再考", "未报考并且不准备考"
    gre_total: Optional[int] = None
    gre_verbal: Optional[int] = None
    gre_quantitative: Optional[int] = None
    gre_writing: Optional[float] = None
    # Target scores for GRE
    gre_target_total: Optional[int] = None
    gre_target_verbal: Optional[int] = None
    gre_target_quantitative: Optional[int] = None
    gre_target_writing: Optional[float] = None
    # Expected test date for GRE
    gre_expected_test_date: Optional[str] = None  # 预期考试时间

    gmat_test_status: Optional[str] = "未报考并且不准备考"  # "已考试", "未报考、准备考", "准备再考", "未报考并且不准备考"
    gmat_total: Optional[int] = None
    # Target scores for GMAT
    gmat_target_total: Optional[int] = None
    # Expected test date for GMAT
    gmat_expected_test_date: Optional[str] = None  # 预期考试时间

    # Experience (optional)
    research_experience_count: Optional[int] = 0
    internship_experience_count: Optional[int] = 0
    work_experience_years: Optional[float] = 0.0

    # Experience details (for compatibility with frontend)
    research_experiences: Optional[List[Dict[str, str]]] = []
    internship_experiences: Optional[List[Dict[str, str]]] = []
    other_experiences: Optional[List[Dict[str, str]]] = []

    # Target information (optional)
    target_countries: Optional[List[str]] = []
    target_majors: Optional[List[str]] = []  # 保持List格式以兼容现有代码，但前端只允许选择一个，数组长度为1
    target_degree_type: Optional[str] = None  # "Master" or "PhD"
    application_year: Optional[int] = None  # 申请年份

    def is_recent_graduate(self) -> Optional[bool]:
        """判断是否为应届生：申请年份和毕业年份相同则为应届生"""
        if self.application_year is None:
            return None
        return self.application_year == self.graduation_year

class CompetitivenessAnalysis(BaseModel):
    strengths: str
    weaknesses: str
    summary: str

class SupportingCase(BaseModel):
    case_id: str
    similarity_score: float
    key_similarities: str

class SchoolRecommendation(BaseModel):
    university: str
    program: str
    reason: str
    supporting_cases: List[SupportingCase]

class SchoolRecommendations(BaseModel):
    recommendations: List[SchoolRecommendation]
    analysis_summary: str

class CaseComparison(BaseModel):
    gpa: str
    university: str
    experience: str

class CaseAnalysis(BaseModel):
    case_id: int
    admitted_university: str
    admitted_program: str
    gpa: str
    language_score: str
    language_test_type: Optional[str] = None  # "TOEFL" or "IELTS"
    key_experiences: Optional[str] = None  # 主要经历摘要
    undergraduate_info: str
    is_recent_graduate: Optional[bool] = None  # 是否是应届生
    comparison: CaseComparison
    success_factors: str
    takeaways: str

class ActionPlan(BaseModel):
    timeframe: str
    action: str
    goal: str

class BackgroundImprovement(BaseModel):
    action_plan: List[ActionPlan]
    strategy_summary: str

class AnalysisReport(BaseModel):
    competitiveness: CompetitivenessAnalysis
    school_recommendations: SchoolRecommendations
    similar_cases: List[CaseAnalysis]
    background_improvement: Optional[BackgroundImprovement] = None
    radar_scores: List[int]  # 雷达图五项能力得分: [学术能力, 语言能力, 科研背景, 实习背景, 院校背景]

# 霍兰德职业兴趣评估相关模型
class HollandAnswer(BaseModel):
    """单个问题的回答"""
    question_id: int
    score: int  # 1-5分

class HollandAssessmentRequest(BaseModel):
    """霍兰德评估请求"""
    answers: List[HollandAnswer]

class HollandTypeScore(BaseModel):
    """单个霍兰德类型的得分"""
    type_code: str  # R, I, A, S, E, C
    type_name: str  # 现实型, 研究型, 艺术型, 社会型, 企业型, 常规型
    score: int
    percentage: float  # 得分百分比

class HollandTypeInterpretation(BaseModel):
    """霍兰德类型解释"""
    type_code: str
    name: str
    nickname: str
    characteristics: str
    typical_careers: List[str]

class HollandAssessmentResult(BaseModel):
    """霍兰德评估结果"""
    holland_code: str  # 三字母代码，如 "RIA"
    type_scores: List[HollandTypeScore]  # 六个类型的得分
    top_three_types: List[HollandTypeInterpretation]  # 前三名类型的详细解释
    assessment_date: str  # 评估日期