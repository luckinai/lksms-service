-- 添加result字段到sms_tasks表
-- 迁移脚本: 002_add_result_field.sql

-- 添加result字段
ALTER TABLE sms_tasks ADD COLUMN IF NOT EXISTS result VARCHAR(500);

-- 添加字段注释
COMMENT ON COLUMN sms_tasks.result IS '最后一次发送汇报结果，失败时记录失败原因';

-- 为现有数据设置默认值（可选）
UPDATE sms_tasks 
SET result = CASE 
    WHEN status = 2 THEN '发送成功'
    WHEN status = 3 THEN '发送失败'
    ELSE NULL
END
WHERE result IS NULL;
