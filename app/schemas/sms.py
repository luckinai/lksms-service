from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SmsRequest(BaseModel):
    """短信发送请求"""
    phone_number: str = Field(..., description="手机号码", min_length=11, max_length=20)
    content: Optional[str] = Field(None, description="发送内容或模板参数", max_length=200)
    use_template: bool = Field(False, description="是否使用模板")
    source: Optional[str] = Field(None, description="来源标识", max_length=50)


class SmsResponse(BaseModel):
    """短信发送响应"""
    task_id: str = Field(..., description="任务ID")
    status: int = Field(..., description="任务状态")


class TaskQueryResponse(BaseModel):
    """任务查询响应"""
    task_id: str = Field(..., description="任务ID")
    phone_number: str = Field(..., description="手机号码")
    content: str = Field(..., description="发送内容")
    status: int = Field(..., description="任务状态")
    created_at: datetime = Field(..., description="创建时间")
    sent_at: Optional[datetime] = Field(None, description="发送时间")


class PendingTaskResponse(BaseModel):
    """待处理任务响应"""
    task_id: str = Field(..., description="任务ID")
    phone_number: str = Field(..., description="手机号码")
    content: str = Field(..., description="发送内容")


class ReportRequest(BaseModel):
    """发送结果汇报请求"""
    task_id: str = Field(..., description="任务ID")
    app_id: str = Field(..., description="APP标识")
    status: int = Field(..., description="发送状态: 2=SUCCESS, 3=FAILED")
    error_message: Optional[str] = Field(None, description="错误信息（失败时）", max_length=500)
    should_retry: bool = Field(False, description="是否应该重试（由APP判断）")


class DefaultSmsRequest(BaseModel):
    """默认短信内容请求"""
    phone_number: str = Field(..., description="手机号码", min_length=11, max_length=20)
    content: str = Field(..., description="默认发送内容", max_length=200)
    use_template: bool = Field(False, description="是否使用模板")


class TemplateRequest(BaseModel):
    """模板创建请求"""
    template_name: str = Field(..., description="模板名称", max_length=100)
    template_content: str = Field(..., description="模板内容，支持{param}占位符", max_length=200)


class PendingTasksResponse(BaseModel):
    """待处理任务列表响应"""
    total_count: int = Field(..., description="获取到的任务总数")
    app_id: str = Field(..., description="请求的APP ID")
    tasks: List[PendingTaskResponse] = Field(..., description="任务列表")


class TaskStatusInfo(BaseModel):
    """任务状态信息"""
    status_code: int = Field(..., description="状态码")
    status_name: str = Field(..., description="状态名称")
    description: str = Field(..., description="状态描述")
