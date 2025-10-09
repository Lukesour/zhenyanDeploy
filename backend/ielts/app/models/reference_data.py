from sqlalchemy import Column, Integer, String, Text, Float, JSON, Boolean, DateTime
from sqlalchemy.sql import func
from backend.ielts.app.core.database import Base

class BandDescriptor(Base):
    """雅思评分标准表"""
    __tablename__ = "band_descriptors"
    
    id = Column(Integer, primary_key=True, index=True)
    dimension = Column(String, nullable=False)  # TR, CC, LR, GRA
    band_score = Column(Float, nullable=False)  # 分数段 (5.0, 5.5, 6.0, etc.)
    task_type = Column(String, nullable=False)  # task1 或 task2
    
    # 评分标准描述
    criteria_text = Column(Text, nullable=False)  # 官方标准文本
    key_features = Column(JSON, nullable=True)  # 关键特征列表
    
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<BandDescriptor(dimension='{self.dimension}', band={self.band_score}, task='{self.task_type}')>"

class SampleEssay(Base):
    """范文库表"""
    __tablename__ = "sample_essays"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    task_type = Column(String, nullable=False)  # task1 或 task2
    essay_type = Column(String, nullable=True)  # Task2题型
    topic = Column(String, nullable=False)  # 主题
    prompt = Column(Text, nullable=False)  # 题目
    content = Column(Text, nullable=False)  # 范文内容
    word_count = Column(Integer, nullable=False)
    
    # 评分信息
    overall_score = Column(Float, nullable=False)
    tr_score = Column(Float, nullable=False)
    cc_score = Column(Float, nullable=False)
    lr_score = Column(Float, nullable=False)
    gra_score = Column(Float, nullable=False)
    
    # 考官评语
    examiner_comment = Column(Text, nullable=True)
    
    # 分析标注
    structure_analysis = Column(JSON, nullable=True)  # 结构分析
    vocabulary_highlights = Column(JSON, nullable=True)  # 词汇亮点
    grammar_features = Column(JSON, nullable=True)  # 语法特色
    
    # 向量嵌入（用于相似度匹配）
    embedding_vector = Column(JSON, nullable=True)  # 存储向量表示
    
    # 元数据
    source = Column(String, nullable=True)  # 来源
    is_verified = Column(Boolean, default=False)  # 是否经过验证
    
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<SampleEssay(id={self.id}, topic='{self.topic}', score={self.overall_score})>"

class VocabularyResource(Base):
    """词汇资源表"""
    __tablename__ = "vocabulary_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 词汇信息
    word = Column(String, nullable=False, index=True)
    word_type = Column(String, nullable=False)  # noun, verb, adjective, etc.
    definition = Column(Text, nullable=True)
    
    # 分类信息
    category = Column(String, nullable=False)  # AWL, academic, topic-specific, etc.
    topic = Column(String, nullable=True)  # 主题分类
    difficulty_level = Column(String, nullable=True)  # beginner, intermediate, advanced
    
    # 使用信息
    collocations = Column(JSON, nullable=True)  # 搭配词组
    synonyms = Column(JSON, nullable=True)  # 同义词
    example_sentences = Column(JSON, nullable=True)  # 例句
    
    # 频率和重要性
    frequency_score = Column(Float, nullable=True)  # 使用频率
    importance_score = Column(Float, nullable=True)  # 重要性评分
    
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<VocabularyResource(word='{self.word}', category='{self.category}')>"

class GrammarRule(Base):
    """语法规则表"""
    __tablename__ = "grammar_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 规则信息
    rule_name = Column(String, nullable=False)
    rule_category = Column(String, nullable=False)  # tense, agreement, article, etc.
    description = Column(Text, nullable=False)
    
    # 错误模式
    error_patterns = Column(JSON, nullable=True)  # 常见错误模式
    correct_examples = Column(JSON, nullable=True)  # 正确示例
    incorrect_examples = Column(JSON, nullable=True)  # 错误示例
    
    # 复杂度和重要性
    complexity_level = Column(String, nullable=False)  # basic, intermediate, advanced
    importance_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<GrammarRule(name='{self.rule_name}', category='{self.rule_category}')>"
