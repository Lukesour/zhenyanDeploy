from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.ielts.app.core.database import Base

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # 用户目标和水平信息
    target_score = Column(Float, nullable=True)  # 目标分数 (5.5-9.0)
    current_level = Column(Float, nullable=True)  # 当前预估水平
    exam_date = Column(DateTime, nullable=True)  # 考试时间
    
    # 账户状态
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    essays = relationship("Essay", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
