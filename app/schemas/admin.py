from typing import List
from pydantic import BaseModel, Field


class RecoveredTaskInfo(BaseModel):
    """恢复的任务信息"""
    task_id: str = Field(..., description="任务ID")
    phone_number: str = Field(..., description="手机号码")
    retry_count: int = Field(..., description="重试次数")
    processing_app_id: str = Field(None, description="处理中的APP ID")


class ZombieTaskRecoveryResponse(BaseModel):
    """僵尸任务恢复响应"""
    recovered_count: int = Field(..., description="恢复的任务数量")
    recovered_tasks: List[RecoveredTaskInfo] = Field(..., description="恢复的任务列表")


class RetryStatisticsResponse(BaseModel):
    """重试统计响应"""
    pending_tasks: int = Field(..., description="待处理任务数量")
    processing_tasks: int = Field(..., description="正在处理任务数量")
    retry_tasks: int = Field(..., description="重试任务数量")
    max_retry_count: int = Field(..., description="最大重试次数配置")
    retry_delay_minutes: int = Field(..., description="重试延迟时间配置（分钟）")
    processing_timeout_minutes: int = Field(..., description="处理超时时间配置（分钟）")


class TemplateResponse(BaseModel):
    """模板响应"""
    id: int = Field(..., description="模板ID")
    template_name: str = Field(..., description="模板名称")
    template_content: str = Field(..., description="模板内容")
    is_active: bool = Field(..., description="是否启用")


class DefaultSmsResponse(BaseModel):
    """默认短信响应"""
    id: int = Field(..., description="记录ID")
    phone_number: str = Field(..., description="手机号码")
    content: str = Field(..., description="默认发送内容")
    use_template: bool = Field(..., description="是否使用模板")
    is_sent: bool = Field(..., description="是否已发送")
