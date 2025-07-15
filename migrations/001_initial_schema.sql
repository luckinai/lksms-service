-- LKSMS Service 数据库初始化脚本
-- 创建时间: 2024-01-01

-- 1. 创建短信模板表
CREATE TABLE IF NOT EXISTS sms_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL,
    template_content VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sms_templates IS '短信模板表';
COMMENT ON COLUMN sms_templates.template_name IS '模板名称';
COMMENT ON COLUMN sms_templates.template_content IS '模板内容，支持{param}占位符';
COMMENT ON COLUMN sms_templates.is_active IS '是否启用';

-- 2. 创建默认短信数据信息表
CREATE TABLE IF NOT EXISTS default_sms_data (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    content VARCHAR(200) NOT NULL,
    use_template BOOLEAN DEFAULT FALSE,
    is_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE default_sms_data IS '默认短信数据信息表';
COMMENT ON COLUMN default_sms_data.phone_number IS '手机号码';
COMMENT ON COLUMN default_sms_data.content IS '默认发送内容';
COMMENT ON COLUMN default_sms_data.use_template IS '是否使用模板';
COMMENT ON COLUMN default_sms_data.is_sent IS '是否已发送';

-- 3. 创建发送任务表
CREATE TABLE IF NOT EXISTS sms_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(50) UNIQUE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    content VARCHAR(200) NOT NULL,
    status INTEGER DEFAULT 0,
    source VARCHAR(50),
    retry_count INTEGER DEFAULT 0,
    processing_app_id VARCHAR(50),
    result VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP WITH TIME ZONE,
    reported_at TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE sms_tasks IS '发送任务表';
COMMENT ON COLUMN sms_tasks.task_id IS '任务ID';
COMMENT ON COLUMN sms_tasks.phone_number IS '手机号码';
COMMENT ON COLUMN sms_tasks.content IS '发送内容';
COMMENT ON COLUMN sms_tasks.status IS '任务状态: 0=PENDING, 1=PROCESSING, 2=SUCCESS, 3=FAILED';
COMMENT ON COLUMN sms_tasks.source IS '来源标识';
COMMENT ON COLUMN sms_tasks.retry_count IS '重试次数';
COMMENT ON COLUMN sms_tasks.processing_app_id IS '处理中的APP ID';
COMMENT ON COLUMN sms_tasks.result IS '最后一次发送汇报结果，失败时记录失败原因';
COMMENT ON COLUMN sms_tasks.sent_at IS '发送时间';
COMMENT ON COLUMN sms_tasks.reported_at IS '汇报时间';

-- 4. 创建接收日志表
CREATE TABLE IF NOT EXISTS receive_logs (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(50),
    phone_number VARCHAR(20),
    content VARCHAR(200),
    use_template BOOLEAN,
    source_ip VARCHAR(45),
    user_agent VARCHAR(500),
    request_data JSONB,
    response_data JSONB,
    status_code INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE receive_logs IS '接收日志表';
COMMENT ON COLUMN receive_logs.request_id IS '请求ID';
COMMENT ON COLUMN receive_logs.phone_number IS '手机号码';
COMMENT ON COLUMN receive_logs.content IS '发送内容';
COMMENT ON COLUMN receive_logs.use_template IS '是否使用模板';
COMMENT ON COLUMN receive_logs.source_ip IS '来源IP';
COMMENT ON COLUMN receive_logs.user_agent IS '用户代理';
COMMENT ON COLUMN receive_logs.request_data IS '完整请求数据';
COMMENT ON COLUMN receive_logs.response_data IS '响应数据';
COMMENT ON COLUMN receive_logs.status_code IS '响应状态码';

-- 5. 创建发送日志表
CREATE TABLE IF NOT EXISTS send_logs (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(50),
    app_id VARCHAR(50),
    phone_number VARCHAR(20),
    content VARCHAR(200),
    request_data JSONB,
    response_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE send_logs IS '发送日志表';
COMMENT ON COLUMN send_logs.task_id IS '任务ID';
COMMENT ON COLUMN send_logs.app_id IS 'APP标识';
COMMENT ON COLUMN send_logs.phone_number IS '手机号码';
COMMENT ON COLUMN send_logs.content IS '发送内容';
COMMENT ON COLUMN send_logs.request_data IS '请求数据';
COMMENT ON COLUMN send_logs.response_data IS '响应数据';

-- 6. 创建汇报日志表
CREATE TABLE IF NOT EXISTS report_logs (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(50),
    app_id VARCHAR(50),
    status INTEGER,
    error_message VARCHAR(500),
    request_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE report_logs IS '汇报日志表';
COMMENT ON COLUMN report_logs.task_id IS '任务ID';
COMMENT ON COLUMN report_logs.app_id IS 'APP标识';
COMMENT ON COLUMN report_logs.status IS '发送状态: 2=SUCCESS, 3=FAILED';
COMMENT ON COLUMN report_logs.error_message IS '错误信息';
COMMENT ON COLUMN report_logs.request_data IS '汇报数据';

-- 7. 创建索引
-- 模板表索引
CREATE INDEX IF NOT EXISTS idx_sms_templates_active ON sms_templates(is_active);

-- 任务表索引
CREATE INDEX IF NOT EXISTS idx_sms_tasks_status ON sms_tasks(status);
CREATE INDEX IF NOT EXISTS idx_sms_tasks_phone ON sms_tasks(phone_number);
CREATE INDEX IF NOT EXISTS idx_sms_tasks_created_at ON sms_tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_sms_tasks_processing_app ON sms_tasks(processing_app_id);

-- 默认短信数据表索引
CREATE INDEX IF NOT EXISTS idx_default_sms_phone ON default_sms_data(phone_number);
CREATE INDEX IF NOT EXISTS idx_default_sms_sent ON default_sms_data(is_sent);

-- 日志表索引
CREATE INDEX IF NOT EXISTS idx_receive_logs_created_at ON receive_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_send_logs_task_id ON send_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_report_logs_task_id ON report_logs(task_id);

-- 8. 插入示例数据
-- 插入示例模板
INSERT INTO sms_templates (template_name, template_content, is_active) VALUES
('验证码模板', '您的验证码是{code}，请在5分钟内使用。', true),
('欢迎模板', '欢迎{name}使用我们的服务！', true)
ON CONFLICT DO NOTHING;

-- 插入示例默认短信内容
INSERT INTO default_sms_data (phone_number, content, use_template, is_sent) VALUES
('13800138000', 'code=123456', true, false),
('13800138001', '欢迎使用我们的服务', false, false)
ON CONFLICT DO NOTHING;
