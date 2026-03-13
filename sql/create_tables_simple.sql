-- ============================================
-- 简化版表结构设计（无触发器，无问题）
-- 所有初始化通过后端代码完成
-- ============================================

-- ============================================
-- 1. API 配置表
-- ============================================
CREATE TABLE IF NOT EXISTS api_config (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    api_key TEXT NOT NULL,
    api_url TEXT NOT NULL,
    model TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

INSERT INTO api_config (api_key, api_url, model)
VALUES (
    'sk-muDiVOc0MZmkpSWMLguFlJhmWRq4707fgKDTfMHSsMPctZxi',
    'https://api.nofx.online/v1/chat/completions',
    'gemini-3.1-flash-image-square'
)
ON CONFLICT DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_api_config_created_at ON api_config(created_at DESC);
ALTER TABLE api_config ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 2. 用户积分表
-- ============================================
CREATE TABLE IF NOT EXISTS user_points (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    current_points INTEGER DEFAULT 0 NOT NULL,
    total_earned INTEGER DEFAULT 0 NOT NULL,
    total_spent INTEGER DEFAULT 0 NOT NULL,
    last_daily_claim DATE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_points_user_id ON user_points(user_id);
ALTER TABLE user_points ENABLE ROW LEVEL SECURITY;

-- 用户只能查看和修改自己的积分记录
CREATE POLICY "Users can view their own points" ON user_points
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own points" ON user_points
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own points" ON user_points
    FOR UPDATE USING (auth.uid() = user_id);

-- ============================================
-- 3. 积分交易记录表
-- ============================================
CREATE TABLE IF NOT EXISTS point_transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    points_change INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    related_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_point_transactions_user_id ON point_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_point_transactions_created_at ON point_transactions(created_at DESC);
ALTER TABLE point_transactions ENABLE ROW LEVEL SECURITY;

-- 用户只能查看自己的交易记录
CREATE POLICY "Users can view their own transactions" ON point_transactions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own transactions" ON point_transactions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================
-- 4. 生成记录表
-- ============================================
CREATE TABLE IF NOT EXISTS generation_records (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    image_data TEXT,
    result_image_url TEXT,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    points_deducted INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_generation_records_user_id ON generation_records(user_id);
CREATE INDEX IF NOT EXISTS idx_generation_records_created_at ON generation_records(created_at DESC);
ALTER TABLE generation_records ENABLE ROW LEVEL SECURITY;

-- 用户只能查看自己的生成记录
CREATE POLICY "Users can view their own generations" ON generation_records
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own generations" ON generation_records
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own generations" ON generation_records
    FOR UPDATE USING (auth.uid() = user_id);

-- ============================================
-- 5. 全局初始配置表
-- ============================================
CREATE TABLE IF NOT EXISTS global_button_templates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    button_label TEXT NOT NULL CHECK (length(button_label) > 0),
    prompt_text TEXT NOT NULL CHECK (length(prompt_text) > 0),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_global_templates_created_at ON global_button_templates(created_at DESC);
ALTER TABLE global_button_templates ENABLE ROW LEVEL SECURITY;

-- 禁止所有用户读取全局模板（通过后端接口复制）
DROP POLICY IF EXISTS "Global templates no access" ON global_button_templates;
CREATE POLICY "Global templates no access"
    ON global_button_templates
    FOR ALL
    USING (false);

-- ============================================
-- 6. 用户私有配置表
-- ============================================
CREATE TABLE IF NOT EXISTS user_buttons (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    button_label TEXT NOT NULL CHECK (length(button_label) > 0),
    prompt_text TEXT NOT NULL CHECK (length(prompt_text) > 0),
    type TEXT NOT NULL CHECK (type IN ('initial', 'custom')),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_buttons_user_id ON user_buttons(user_id);
CREATE INDEX IF NOT EXISTS idx_user_buttons_created_at ON user_buttons(user_id, created_at DESC);
ALTER TABLE user_buttons ENABLE ROW LEVEL SECURITY;

-- 用户可以读取自己的配置
DROP POLICY IF EXISTS "Users can view own buttons" ON user_buttons;
CREATE POLICY "Users can view own buttons"
    ON user_buttons
    FOR SELECT
    USING (auth.uid() = user_id);

-- 用户可以插入自己的配置
DROP POLICY IF EXISTS "Users can insert own buttons" ON user_buttons;
CREATE POLICY "Users can insert own buttons"
    ON user_buttons
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- 用户可以更新自己的配置
DROP POLICY IF EXISTS "Users can update own buttons" ON user_buttons;
CREATE POLICY "Users can update own buttons"
    ON user_buttons
    FOR UPDATE
    USING (auth.uid() = user_id);

-- 用户可以删除自己的配置
DROP POLICY IF EXISTS "Users can delete own buttons" ON user_buttons;
CREATE POLICY "Users can delete own buttons"
    ON user_buttons
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- 7. 插入默认全局模板
-- ============================================
INSERT INTO global_button_templates (button_label, prompt_text) VALUES
('优化图片', '请优化这张图片，使其更清晰、色彩更鲜艳'),
('去除背景', '请帮我去除这张图片的背景，只保留主体'),
('增强细节', '请增强这张图片的细节，让画面更清晰'),
('风格转换-油画', '请将这张图片转换为油画风格'),
('风格转换-水彩', '请将这张图片转换为水彩画风格'),
('黑白照片', '请将这张图片转换为高质量黑白照片'),
('修复老照片', '请修复这张老照片，改善画质和色彩'),
('AI 生成补充', '根据图片内容，AI 生成补充画面，使其更完整')
ON CONFLICT DO NOTHING;
