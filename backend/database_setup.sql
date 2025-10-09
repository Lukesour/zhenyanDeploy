-- 箴言留学用户系统数据库表创建脚本
-- 请在Supabase SQL编辑器中执行此脚本

-- 1. 创建用户表
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

-- 2. 创建邮箱验证码表
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

-- 3. 创建邀请码表
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

-- 4. 创建用户分析记录表
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

-- 5. 创建用户个人信息表
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
    language_test_status VARCHAR(30) NOT NULL DEFAULT '未报考并且不准备考', -- 已考试, 未报考、准备考, 准备再考, 未报考并且不准备考
    language_test_type VARCHAR(20), -- TOEFL, IELTS
    language_total_score DECIMAL(5,1),
    language_reading DECIMAL(5,1),
    language_listening DECIMAL(5,1),
    language_speaking DECIMAL(5,1),
    language_writing DECIMAL(5,1),
    -- 目标分数（用于未报考、准备考和准备再考状态）
    language_target_total_score DECIMAL(5,1),
    language_target_reading DECIMAL(5,1),
    language_target_listening DECIMAL(5,1),
    language_target_speaking DECIMAL(5,1),
    language_target_writing DECIMAL(5,1),
    -- 考试时间（用于未报考、准备考和准备再考状态）
    language_expected_test_date DATE, -- 预期考试时间

    -- 标准化考试成绩
    gre_test_status VARCHAR(30) DEFAULT '未报考并且不准备考', -- 已考试, 未报考、准备考, 准备再考, 未报考并且不准备考
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
    gre_expected_test_date DATE, -- 预期考试时间

    gmat_test_status VARCHAR(30) DEFAULT '未报考并且不准备考', -- 已考试, 未报考、准备考, 准备再考, 未报考并且不准备考
    gmat_total INTEGER,
    -- GMAT目标分数
    gmat_target_total INTEGER,
    -- GMAT考试时间
    gmat_expected_test_date DATE, -- 预期考试时间

    -- 目标信息
    target_countries JSONB, -- 数组格式
    target_majors JSONB, -- 数组格式
    target_degree_type VARCHAR(20), -- Master, PhD
    application_year INTEGER,

    -- 经历信息
    research_experiences JSONB, -- 数组格式，包含详细信息
    internship_experiences JSONB, -- 数组格式，包含详细信息
    other_experiences JSONB, -- 数组格式，包含详细信息

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_invitation_code ON users(invitation_code);
CREATE INDEX IF NOT EXISTS idx_users_invited_by_code ON users(invited_by_code);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

CREATE INDEX IF NOT EXISTS idx_email_verification_codes_email ON email_verification_codes(email);
CREATE INDEX IF NOT EXISTS idx_email_verification_codes_phone ON email_verification_codes(phone);
CREATE INDEX IF NOT EXISTS idx_email_verification_codes_code ON email_verification_codes(code);
CREATE INDEX IF NOT EXISTS idx_email_verification_codes_expires_at ON email_verification_codes(expires_at);

CREATE INDEX IF NOT EXISTS idx_invitation_codes_code ON invitation_codes(code);
CREATE INDEX IF NOT EXISTS idx_invitation_codes_user_id ON invitation_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_invitation_codes_status ON invitation_codes(status);

CREATE INDEX IF NOT EXISTS idx_user_analysis_records_user_id ON user_analysis_records(user_id);
CREATE INDEX IF NOT EXISTS idx_user_analysis_records_task_id ON user_analysis_records(task_id);
CREATE INDEX IF NOT EXISTS idx_user_analysis_records_status ON user_analysis_records(status);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_undergraduate_university ON user_profiles(undergraduate_university);
CREATE INDEX IF NOT EXISTS idx_user_profiles_target_degree_type ON user_profiles(target_degree_type);

-- 7. 创建触发器以自动更新updated_at字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 8. 插入一些测试数据（可选）
-- INSERT INTO users (phone, email, status, invitation_code, email_verified) VALUES
-- ('13800138000', 'test@example.com', 'active', 'TEST1234', true);

-- 9. 创建RLS (Row Level Security) 策略（可选，用于数据安全）
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE email_verification_codes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE invitation_codes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_analysis_records ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- 创建策略示例（用户只能访问自己的数据）
-- CREATE POLICY "Users can view own data" ON users
--     FOR SELECT USING (auth.uid()::text = id::text);

-- CREATE POLICY "Users can update own data" ON users
--     FOR UPDATE USING (auth.uid()::text = id::text);

-- 10. 创建视图以便于查询用户统计信息
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.phone,
    u.email,
    u.status,
    u.remaining_analyses,
    u.total_analyses_used,
    u.invitation_code,
    u.invited_count,
    u.created_at,
    u.last_login_at,
    COALESCE(ic.used_count, 0) as invitation_used_count,
    (u.invited_count * 3) as total_earned_analyses
FROM users u
LEFT JOIN invitation_codes ic ON u.invitation_code = ic.code;

-- 11. 创建函数以便于邀请码处理
CREATE OR REPLACE FUNCTION process_invitation_usage(
    invitation_code_param VARCHAR(20),
    new_user_id_param INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
    inviter_user_id INTEGER;
BEGIN
    -- 获取邀请者ID
    SELECT user_id INTO inviter_user_id 
    FROM invitation_codes 
    WHERE code = invitation_code_param AND status = 'active';
    
    IF inviter_user_id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- 更新邀请码使用次数
    UPDATE invitation_codes 
    SET used_count = used_count + 1 
    WHERE code = invitation_code_param;
    
    -- 给邀请者增加分析次数和邀请计数
    UPDATE users 
    SET 
        remaining_analyses = remaining_analyses + 3,
        invited_count = invited_count + 1
    WHERE id = inviter_user_id;
    
    -- 更新被邀请用户的invited_by_code
    UPDATE users 
    SET invited_by_code = invitation_code_param 
    WHERE id = new_user_id_param;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- 12. 创建清理过期验证码的函数
CREATE OR REPLACE FUNCTION cleanup_expired_verification_codes() 
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM email_verification_codes 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 13. 创建定时任务清理过期验证码（需要pg_cron扩展）
-- SELECT cron.schedule('cleanup-verification-codes', '0 * * * *', 'SELECT cleanup_expired_verification_codes();');

-- 执行完成提示
SELECT 'Database setup completed successfully!' as message;
