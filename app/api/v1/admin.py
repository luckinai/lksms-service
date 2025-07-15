from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import verify_credentials
from app.services.sms_service import SmsService
from app.services.template_service import TemplateService

from app.services.scheduler_service import scheduler
from app.schemas.sms import DefaultSmsRequest, TemplateRequest, TaskStatusInfo
from app.schemas.admin import (
    ZombieTaskRecoveryResponse,
    TaskStatisticsResponse,
    TemplateResponse,
    DefaultSmsResponse
)
from app.schemas.response import ApiResponse

router = APIRouter()


@router.post("/template", response_model=ApiResponse[TemplateResponse])
async def create_template(
    template_request: TemplateRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    """创建短信模板"""
    template_service = TemplateService(db)

    try:
        template = await template_service.create_template(
            template_name=template_request.template_name,
            template_content=template_request.template_content
        )

        response_data = TemplateResponse(
            id=template.id,
            template_name=template.template_name,
            template_content=template.template_content,
            is_active=template.is_active
        )

        return ApiResponse(data=response_data, message="模板创建成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模板创建失败: {str(e)}")


@router.post("/default-sms", response_model=ApiResponse[DefaultSmsResponse])
async def create_default_sms(
    default_sms_request: DefaultSmsRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    """添加默认短信内容"""
    sms_service = SmsService(db)

    try:
        default_sms = await sms_service.create_default_sms(
            phone_number=default_sms_request.phone_number,
            content=default_sms_request.content,
            use_template=default_sms_request.use_template
        )

        response_data = DefaultSmsResponse(
            id=default_sms.id,
            phone_number=default_sms.phone_number,
            content=default_sms.content,
            use_template=default_sms.use_template,
            is_sent=default_sms.is_sent
        )

        return ApiResponse(data=response_data, message="默认短信内容添加成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加失败: {str(e)}")


@router.post("/recover-zombie-tasks", response_model=ApiResponse[ZombieTaskRecoveryResponse])
async def recover_zombie_tasks(
    _: str = Depends(verify_credentials)
):
    """手动恢复僵尸任务"""
    try:
        result = await scheduler.manual_recover_zombie_tasks()

        response_data = ZombieTaskRecoveryResponse(
            recovered_count=result["recovered_count"],
            message=result["message"]
        )

        return ApiResponse(data=response_data, message=f"成功恢复 {result['recovered_count']} 个僵尸任务")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复僵尸任务失败: {str(e)}")


@router.get("/task-statistics", response_model=ApiResponse[TaskStatisticsResponse])
async def get_task_statistics(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_credentials)
):
    """获取任务统计信息"""
    try:
        sms_service = SmsService(db)
        stats = await sms_service.get_task_statistics()

        return ApiResponse(data=stats, message="获取统计信息成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/task-status-info", response_model=ApiResponse[List[TaskStatusInfo]])
async def get_task_status_info(
    _: str = Depends(verify_credentials)
):
    """获取任务状态信息"""
    from app.utils.enums import TaskStatus

    status_info = [
        TaskStatusInfo(
            status_code=TaskStatus.PENDING,
            status_name="PENDING",
            description=TaskStatus.get_description(TaskStatus.PENDING)
        ),
        TaskStatusInfo(
            status_code=TaskStatus.PROCESSING,
            status_name="PROCESSING",
            description=TaskStatus.get_description(TaskStatus.PROCESSING)
        ),
        TaskStatusInfo(
            status_code=TaskStatus.SUCCESS,
            status_name="SUCCESS",
            description=TaskStatus.get_description(TaskStatus.SUCCESS)
        ),
        TaskStatusInfo(
            status_code=TaskStatus.FAILED,
            status_name="FAILED",
            description=TaskStatus.get_description(TaskStatus.FAILED)
        )
    ]

    return ApiResponse(data=status_info, message="获取任务状态信息成功")
