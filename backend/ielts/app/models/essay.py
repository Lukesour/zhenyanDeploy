from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from backend.ielts.app.core.database import Base
from backend.ielts.app.models.user import User  # Ensure mapper registry knows about User

class TaskType(str, Enum):
    """作文任务类型"""
    TASK1 = "task1"
    TASK2 = "task2"

class EssayType(str, Enum):
    """Task 2 作文题型"""
    AGREE_DISAGREE = "agree_disagree"
    DISCUSS_BOTH = "discuss_both"
    ADVANTAGES_DISADVANTAGES = "advantages_disadvantages"
    PROBLEM_SOLUTION = "problem_solution"
    TWO_PART_QUESTION = "two_part_question"

class Essay(Base):
    """作文表"""
    __tablename__ = "essays"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 作文基本信息
    task_type = Column(String, nullable=False)  # task1 或 task2
    essay_type = Column(String, nullable=True)  # 仅Task2需要，题型分类
    title = Column(Text, nullable=False)  # 作文题目
    content = Column(Text, nullable=False)  # 作文内容
    word_count = Column(Integer, nullable=False)  # 字数统计
    
    # 题目解析结果
    prompt_analysis = Column(JSON, nullable=True)  # 题目解析JSON
    
    # 评分状态
    is_graded = Column(Boolean, default=False)
    grading_status = Column(String, default="pending")  # pending, processing, completed, failed
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="essays")
    grading_result = relationship("GradingResult", back_populates="essay", uselist=False)
    
    def __repr__(self):
        return f"<Essay(id={self.id}, user_id={self.user_id}, task_type='{self.task_type}')>"

class GradingResult(Base):
    """评分结果表"""
    __tablename__ = "grading_results"
    
    id = Column(Integer, primary_key=True, index=True)
    essay_id = Column(Integer, ForeignKey("essays.id"), nullable=False)
    
    # 四个维度分数
    tr_score = Column(Float, nullable=False)  # Task Response/Achievement
    cc_score = Column(Float, nullable=False)  # Coherence and Cohesion
    lr_score = Column(Float, nullable=False)  # Lexical Resource
    gra_score = Column(Float, nullable=False)  # Grammatical Range and Accuracy
    
    # 总分
    overall_score = Column(Float, nullable=False)
    
    # 详细分析结果
    tr_analysis = Column(JSON, nullable=True)  # TR维度详细分析
    cc_analysis = Column(JSON, nullable=True)  # CC维度详细分析
    lr_analysis = Column(JSON, nullable=True)  # LR维度详细分析
    gra_analysis = Column(JSON, nullable=True)  # GRA维度详细分析
    
    # 综合评语和建议
    overall_comment = Column(Text, nullable=True)  # 总评
    improvement_suggestions = Column(JSON, nullable=True)  # 改进建议列表
    
    # 使用的模型信息
    model_used = Column(String, nullable=False)  # 使用的AI模型
    processing_time = Column(Float, nullable=True)  # 处理时间（秒）
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    essay = relationship("Essay", back_populates="grading_result")
    
    def __repr__(self):
        return f"<GradingResult(id={self.id}, essay_id={self.essay_id}, overall_score={self.overall_score})>"
