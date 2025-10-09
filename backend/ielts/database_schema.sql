-- IELTS Essay Grading System Database Schema
-- PostgreSQL Database Schema

-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    target_score DECIMAL(2,1) CHECK (target_score >= 1.0 AND target_score <= 9.0),
    current_level DECIMAL(2,1) CHECK (current_level >= 1.0 AND current_level <= 9.0),
    exam_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 作文表
CREATE TABLE essays (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    task_type VARCHAR(10) NOT NULL CHECK (task_type IN ('task1', 'task2')),
    essay_type VARCHAR(50), -- 仅Task2需要
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    prompt_analysis JSONB,
    is_graded BOOLEAN DEFAULT FALSE,
    grading_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 评分结果表
CREATE TABLE grading_results (
    id SERIAL PRIMARY KEY,
    essay_id INTEGER REFERENCES essays(id) ON DELETE CASCADE,
    tr_score DECIMAL(2,1) NOT NULL CHECK (tr_score >= 1.0 AND tr_score <= 9.0),
    cc_score DECIMAL(2,1) NOT NULL CHECK (cc_score >= 1.0 AND cc_score <= 9.0),
    lr_score DECIMAL(2,1) NOT NULL CHECK (lr_score >= 1.0 AND lr_score <= 9.0),
    gra_score DECIMAL(2,1) NOT NULL CHECK (gra_score >= 1.0 AND gra_score <= 9.0),
    overall_score DECIMAL(2,1) NOT NULL CHECK (overall_score >= 1.0 AND overall_score <= 9.0),
    tr_analysis JSONB,
    cc_analysis JSONB,
    lr_analysis JSONB,
    gra_analysis JSONB,
    overall_comment TEXT,
    improvement_suggestions JSONB,
    model_used VARCHAR(100) NOT NULL,
    processing_time DECIMAL(10,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 评分标准表
CREATE TABLE band_descriptors (
    id SERIAL PRIMARY KEY,
    dimension VARCHAR(10) NOT NULL CHECK (dimension IN ('TR', 'TA', 'CC', 'LR', 'GRA')),
    band_score DECIMAL(2,1) NOT NULL CHECK (band_score >= 1.0 AND band_score <= 9.0),
    task_type VARCHAR(10) NOT NULL CHECK (task_type IN ('task1', 'task2')),
    criteria_text TEXT NOT NULL,
    key_features JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dimension, band_score, task_type)
);

-- 范文库表
CREATE TABLE sample_essays (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(10) NOT NULL CHECK (task_type IN ('task1', 'task2')),
    essay_type VARCHAR(50),
    topic VARCHAR(255) NOT NULL,
    prompt TEXT NOT NULL,
    content TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    overall_score DECIMAL(2,1) NOT NULL CHECK (overall_score >= 1.0 AND overall_score <= 9.0),
    tr_score DECIMAL(2,1) NOT NULL CHECK (tr_score >= 1.0 AND tr_score <= 9.0),
    cc_score DECIMAL(2,1) NOT NULL CHECK (cc_score >= 1.0 AND cc_score <= 9.0),
    lr_score DECIMAL(2,1) NOT NULL CHECK (lr_score >= 1.0 AND lr_score <= 9.0),
    gra_score DECIMAL(2,1) NOT NULL CHECK (gra_score >= 1.0 AND gra_score <= 9.0),
    examiner_comment TEXT,
    structure_analysis JSONB,
    vocabulary_highlights JSONB,
    grammar_features JSONB,
    embedding_vector JSONB,
    source VARCHAR(255),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 词汇资源表
CREATE TABLE vocabulary_resources (
    id SERIAL PRIMARY KEY,
    word VARCHAR(255) NOT NULL,
    word_type VARCHAR(50) NOT NULL,
    definition TEXT,
    category VARCHAR(100) NOT NULL,
    topic VARCHAR(100),
    difficulty_level VARCHAR(20),
    collocations JSONB,
    synonyms JSONB,
    example_sentences JSONB,
    frequency_score DECIMAL(5,3),
    importance_score DECIMAL(5,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 语法规则表
CREATE TABLE grammar_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(255) NOT NULL,
    rule_category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    error_patterns JSONB,
    correct_examples JSONB,
    incorrect_examples JSONB,
    complexity_level VARCHAR(20) NOT NULL,
    importance_score DECIMAL(5,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_essays_user_id ON essays(user_id);
CREATE INDEX idx_essays_task_type ON essays(task_type);
CREATE INDEX idx_essays_created_at ON essays(created_at);
CREATE INDEX idx_grading_results_essay_id ON grading_results(essay_id);
CREATE INDEX idx_sample_essays_task_type ON sample_essays(task_type);
CREATE INDEX idx_sample_essays_topic ON sample_essays(topic);
CREATE INDEX idx_sample_essays_overall_score ON sample_essays(overall_score);
CREATE INDEX idx_vocabulary_word ON vocabulary_resources(word);
CREATE INDEX idx_vocabulary_category ON vocabulary_resources(category);
CREATE INDEX idx_grammar_category ON grammar_rules(rule_category);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表创建更新时间触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_essays_updated_at BEFORE UPDATE ON essays
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
