from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserStatus(str, Enum):
    """用户状态枚举"""
    PENDING = "pending"  # 待验证
    ACTIVE = "active"    # 已激活
    SUSPENDED = "suspended"  # 已暂停
    DELETED = "deleted"  # 已删除

class InvitationStatus(str, Enum):
    """邀请码状态枚举"""
    ACTIVE = "active"    # 有效
    USED = "used"        # 已使用
    EXPIRED = "expired"  # 已过期

# === 请求模型 ===

class UserProfileData(BaseModel):
    """用户个人信息数据"""
    # 学术背景
    undergraduate_university: Optional[str] = None
    undergraduate_major: Optional[str] = None
    gpa: Optional[float] = None
    gpa_scale: Optional[str] = None
    graduation_year: Optional[int] = None
    target_score: Optional[float] = None
    current_level: Optional[float] = None
    exam_date: Optional[str] = None

    # 语言成绩
    language_test_status: Optional[str] = None  # 已考试, 未报考、准备考, 准备再考, 未报考并且不准备考
    language_test_type: Optional[str] = None  # TOEFL, IELTS
    language_total_score: Optional[float] = None
    language_reading: Optional[float] = None
    language_listening: Optional[float] = None
    language_speaking: Optional[float] = None
    language_writing: Optional[float] = None
    # 语言考试目标分数
    language_target_total_score: Optional[float] = None
    language_target_reading: Optional[float] = None
    language_target_listening: Optional[float] = None
    language_target_speaking: Optional[float] = None
    language_target_writing: Optional[float] = None
    # 语言考试时间
    language_expected_test_date: Optional[str] = None  # 预期考试时间

    # 标准化考试成绩
    gre_test_status: Optional[str] = None  # 已考试, 未报考、准备考, 准备再考, 未报考并且不准备考
    gre_total: Optional[int] = None
    gre_verbal: Optional[int] = None
    gre_quantitative: Optional[int] = None
    gre_writing: Optional[float] = None
    # GRE目标分数
    gre_target_total: Optional[int] = None
    gre_target_verbal: Optional[int] = None
    gre_target_quantitative: Optional[int] = None
    gre_target_writing: Optional[float] = None
    # GRE考试时间
    gre_expected_test_date: Optional[str] = None  # 预期考试时间

    gmat_test_status: Optional[str] = None  # 已考试, 未报考、准备考, 准备再考, 未报考并且不准备考
    gmat_total: Optional[int] = None
    # GMAT目标分数
    gmat_target_total: Optional[int] = None
    # GMAT考试时间
    gmat_expected_test_date: Optional[str] = None  # 预期考试时间

    # 目标信息
    target_countries: Optional[List[str]] = []
    target_majors: Optional[List[str]] = []
    target_degree_type: Optional[str] = None  # Master, PhD
    application_year: Optional[int] = None

    # 经历信息
    research_experiences: Optional[List[dict]] = []
    internship_experiences: Optional[List[dict]] = []
    other_experiences: Optional[List[dict]] = []

class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    phone: str
    email: EmailStr
    verification_code: str
    invitation_code: Optional[str] = None
    profile_data: Optional[UserProfileData] = None  # 新增个人信息字段

    @validator('phone')
    def validate_phone(cls, v):
        # 简单的中国手机号验证
        if not v.startswith(('13', '14', '15', '16', '17', '18', '19')):
            raise ValueError('请输入有效的中国大陆手机号')
        if len(v) != 11:
            raise ValueError('手机号必须是11位数字')
        if not v.isdigit():
            raise ValueError('手机号只能包含数字')
        return v

class UserLoginRequest(BaseModel):
    """用户登录请求"""
    phone: str
    email: EmailStr
    verification_code: str
    profile_data: Optional[UserProfileData] = None  # 个人信息数据，用于自动创建账户时保存

class SendVerificationCodeRequest(BaseModel):
    """发送验证码请求"""
    email: EmailStr
    phone: str

    @validator('phone')
    def validate_phone(cls, v):
        if not v.startswith(('13', '14', '15', '16', '17', '18', '19')):
            raise ValueError('请输入有效的中国大陆手机号')
        if len(v) != 11:
            raise ValueError('手机号必须是11位数字')
        if not v.isdigit():
            raise ValueError('手机号只能包含数字')
        return v

class UseInvitationRequest(BaseModel):
    """使用邀请码请求"""
    invitation_code: str

# === 响应模型 ===

class UserInfo(BaseModel):
    """用户信息响应"""
    id: int
    phone: str
    email: str
    status: UserStatus
    remaining_analyses: int
    total_analyses_used: int
    invitation_code: Optional[str]
    invited_count: int
    created_at: datetime
    last_login_at: Optional[datetime]
    profile_data: Optional[UserProfileData] = None  # 新增个人信息字段

class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: UserInfo
    is_new_user: Optional[bool] = False  # 标识是否为新创建的用户

class InvitationCodeInfo(BaseModel):
    """邀请码信息"""
    code: str
    status: InvitationStatus
    used_count: int
    max_uses: int
    created_at: datetime
    expires_at: Optional[datetime]

# === 数据库模型 ===

class User(BaseModel):
    """用户数据库模型"""
    id: Optional[int] = None
    phone: str
    email: str
    status: UserStatus = UserStatus.PENDING
    remaining_analyses: int = 3  # 默认3次分析机会
    total_analyses_used: int = 0
    invitation_code: Optional[str] = None  # 用户自己的邀请码
    invited_by_code: Optional[str] = None  # 被哪个邀请码邀请
    invited_count: int = 0  # 邀请的用户数量
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    email_verified: bool = False

class UserProfile(BaseModel):
    """用户个人信息数据库模型"""
    id: Optional[int] = None
    user_id: int

    # 学术背景
    undergraduate_university: Optional[str] = None
    undergraduate_major: Optional[str] = None
    gpa: Optional[float] = None
    gpa_scale: Optional[str] = None
    graduation_year: Optional[int] = None
    target_score: Optional[float] = None
    current_level: Optional[float] = None
    exam_date: Optional[str] = None

    # 语言成绩
    language_test_status: Optional[str] = None  # 已考试, 未报考, 准备再考
    language_test_type: Optional[str] = None
    language_total_score: Optional[float] = None
    language_reading: Optional[float] = None
    language_listening: Optional[float] = None
    language_speaking: Optional[float] = None
    language_writing: Optional[float] = None
    # 语言考试目标分数
    language_target_total_score: Optional[float] = None
    language_target_reading: Optional[float] = None
    language_target_listening: Optional[float] = None
    language_target_speaking: Optional[float] = None
    language_target_writing: Optional[float] = None
    language_expected_test_date: Optional[str] = None

    # 标准化考试成绩
    gre_test_status: Optional[str] = None  # 已考试, 未报考, 准备再考
    gre_total: Optional[int] = None
    gre_verbal: Optional[int] = None
    gre_quantitative: Optional[int] = None
    gre_writing: Optional[float] = None
    # GRE目标分数
    gre_target_total: Optional[int] = None
    gre_target_verbal: Optional[int] = None
    gre_target_quantitative: Optional[int] = None
    gre_target_writing: Optional[float] = None
    gre_expected_test_date: Optional[str] = None

    gmat_test_status: Optional[str] = None  # 已考试, 未报考, 准备再考
    gmat_total: Optional[int] = None
    # GMAT目标分数
    gmat_target_total: Optional[int] = None
    gmat_expected_test_date: Optional[str] = None

    # 目标信息
    target_countries: Optional[List[str]] = []
    target_majors: Optional[List[str]] = []
    target_degree_type: Optional[str] = None
    application_year: Optional[int] = None

    # 经历信息
    research_experiences: Optional[List[dict]] = []
    internship_experiences: Optional[List[dict]] = []
    other_experiences: Optional[List[dict]] = []

    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EmailVerificationCode(BaseModel):
    """邮箱验证码数据库模型"""
    id: Optional[int] = None
    email: str
    phone: str
    code: str
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    used: bool = False
    used_at: Optional[datetime] = None

class InvitationCode(BaseModel):
    """邀请码数据库模型"""
    id: Optional[int] = None
    code: str
    user_id: int  # 邀请码所属用户
    status: InvitationStatus = InvitationStatus.ACTIVE
    used_count: int = 0
    max_uses: int = 999  # 最大使用次数，默认999次
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class UserAnalysisRecord(BaseModel):
    """用户分析记录数据库模型"""
    id: Optional[int] = None
    user_id: int
    task_id: str  # 分析任务ID
    analysis_data: Optional[dict] = None  # 分析请求数据
    analysis_result: Optional[dict] = None  # 分析结果
    status: str = "pending"  # pending, completed, failed
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# === 数据库表创建SQL ===

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(11) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    remaining_analyses INTEGER DEFAULT 3,
    total_analyses_used INTEGER DEFAULT 0,
    invitation_code VARCHAR(20) UNIQUE,
    invited_by_code VARCHAR(20),
    invited_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    email_verified BOOLEAN DEFAULT FALSE
);
"""

CREATE_EMAIL_VERIFICATION_CODES_TABLE = """
CREATE TABLE IF NOT EXISTS email_verification_codes (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(11) NOT NULL,
    code VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP
);
"""

CREATE_INVITATION_CODES_TABLE = """
CREATE TABLE IF NOT EXISTS invitation_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'active',
    used_count INTEGER DEFAULT 0,
    max_uses INTEGER DEFAULT 999,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
"""

CREATE_USER_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- 学术背景
    undergraduate_university VARCHAR(255),
    undergraduate_major VARCHAR(255),
    gpa DECIMAL(4,2),
    gpa_scale VARCHAR(10),
    graduation_year INTEGER,
    target_score DECIMAL(3,1),
    current_level DECIMAL(3,1),
    exam_date DATE,

    -- 语言成绩
    language_test_status VARCHAR(30) NOT NULL DEFAULT '未报考并且不准备考',
    language_test_type VARCHAR(20),
    language_total_score DECIMAL(5,1),
    language_reading DECIMAL(5,1),
    language_listening DECIMAL(5,1),
    language_speaking DECIMAL(5,1),
    language_writing DECIMAL(5,1),
    -- 语言考试目标分数
    language_target_total_score DECIMAL(5,1),
    language_target_reading DECIMAL(5,1),
    language_target_listening DECIMAL(5,1),
    language_target_speaking DECIMAL(5,1),
    language_target_writing DECIMAL(5,1),
    -- 语言考试时间
    language_expected_test_date DATE,

    -- 标准化考试成绩
    gre_test_status VARCHAR(30) DEFAULT '未报考并且不准备考',
    gre_total INTEGER,
    gre_verbal INTEGER,
    gre_quantitative INTEGER,
    gre_writing DECIMAL(3,1),
    -- GRE目标分数
    gre_target_total INTEGER,
    gre_target_verbal INTEGER,
    gre_target_quantitative INTEGER,
    gre_target_writing DECIMAL(3,1),
    -- GRE考试时间
    gre_expected_test_date DATE,

    gmat_test_status VARCHAR(30) DEFAULT '未报考并且不准备考',
    gmat_total INTEGER,
    -- GMAT目标分数
    gmat_target_total INTEGER,
    -- GMAT考试时间
    gmat_expected_test_date DATE,

    -- 目标信息
    target_countries JSONB,
    target_majors JSONB,
    target_degree_type VARCHAR(20),
    application_year INTEGER,

    -- 经历信息
    research_experiences JSONB,
    internship_experiences JSONB,
    other_experiences JSONB,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_USER_ANALYSIS_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS user_analysis_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    analysis_data JSONB,
    analysis_result JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
"""

# 创建索引
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);",
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
    "CREATE INDEX IF NOT EXISTS idx_users_invitation_code ON users(invitation_code);",
    "CREATE INDEX IF NOT EXISTS idx_email_verification_codes_email ON email_verification_codes(email);",
    "CREATE INDEX IF NOT EXISTS idx_email_verification_codes_phone ON email_verification_codes(phone);",
    "CREATE INDEX IF NOT EXISTS idx_invitation_codes_code ON invitation_codes(code);",
    "CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_user_profiles_undergraduate_university ON user_profiles(undergraduate_university);",
    "CREATE INDEX IF NOT EXISTS idx_user_profiles_target_degree_type ON user_profiles(target_degree_type);",
    "CREATE INDEX IF NOT EXISTS idx_user_analysis_records_user_id ON user_analysis_records(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_user_analysis_records_task_id ON user_analysis_records(task_id);"
]

# 所有建表语句
ALL_CREATE_STATEMENTS = [
    CREATE_USERS_TABLE,
    CREATE_EMAIL_VERIFICATION_CODES_TABLE,
    CREATE_INVITATION_CODES_TABLE,
    CREATE_USER_PROFILES_TABLE,
    CREATE_USER_ANALYSIS_RECORDS_TABLE
] + CREATE_INDEXES
