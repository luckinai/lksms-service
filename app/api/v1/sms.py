from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import verify_credentials
from app.services.sms_service import SmsService
from app.services.log_service import LogService
from app.schemas.sms import (
    SmsRequest, SmsResponse, TaskQueryResponse,
    PendingTaskResponse, ReportRequest, PendingTasksResponse
)
from app.schemas.response import ApiResponse
from app.utils.enums import TaskStatus
from app.utils.helpers import generate_request_id

router = APIRouter()


@router.post("/send", response_model=ApiResponse[SmsResponse])
async def send_sms(
    request: Request,
    sms_request: SmsRequest,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """提交短信发送任务"""
    request_id = generate_request_id()
    sms_service = SmsService(db)
    log_service = LogService(db)
    
    try:
        # 创建任务
        task = await sms_service.create_task(
            phone_number=sms_request.phone_number,
            content=sms_request.content,
            use_template=sms_request.use_template,
            source=sms_request.source
        )
        
        response_data = SmsResponse(
            task_id=task.task_id,
            status=task.status,
        )
        
        # 记录接收日志
        await log_service.log_receive(
            request_id=request_id,
            phone_number=sms_request.phone_number,
            content=sms_request.content,
            use_template=sms_request.use_template,
            source_ip=request.client.host if request.client else "",
            user_agent=request.headers.get("user-agent", ""),
            request_data=sms_request.model_dump(),
            response_data=response_data.model_dump(),
            status_code=200
        )
        
        return ApiResponse(data=response_data)
        
    except ValueError as e:
        # 记录错误日志
        await log_service.log_receive(
            request_id=request_id,
            phone_number=sms_request.phone_number,
            content=sms_request.content,
            use_template=sms_request.use_template,
            source_ip=request.client.host if request.client else "",
            user_agent=request.headers.get("user-agent", ""),
            request_data=sms_request.model_dump(),
            response_data={"error": str(e)},
            status_code=400
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/task/{task_id}", response_model=ApiResponse[TaskQueryResponse])
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """查询任务状态"""
    sms_service = SmsService(db)
    
    task = await sms_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    response_data = TaskQueryResponse(
        task_id=task.task_id,
        phone_number=task.phone_number,
        content=task.content,
        status=task.status,
        created_at=task.created_at,
        sent_at=task.sent_at
    )
    
    return ApiResponse(data=response_data)


@router.get("/tasks/pending", response_model=ApiResponse[PendingTasksResponse])
async def get_pending_tasks(
    app_id: str = Query(..., description="APP标识"),
    limit: int = Query(10, ge=1, le=100, description="获取数量限制"),
    db: AsyncSession = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """获取待发送任务（并发安全）"""
    sms_service = SmsService(db)
    log_service = LogService(db)

    tasks = await sms_service.get_pending_tasks_safely(app_id, limit)

    task_list = [
        PendingTaskResponse(
            task_id=task.task_id,
            phone_number=task.phone_number,
            content=task.content
        )
        for task in tasks
    ]

    response_data = PendingTasksResponse(
        total_count=len(task_list),
        app_id=app_id,
        tasks=task_list
    )

    # 记录发送日志
    for task in tasks:
        await log_service.log_send(
            task_id=task.task_id,
            app_id=app_id,
            phone_number=task.phone_number,
            content=task.content,
            request_data={"app_id": app_id, "limit": limit},
            response_data={"task_count": len(tasks)}
        )

    return ApiResponse(data=response_data)


@router.post("/report", response_model=ApiResponse[None])
async def report_result(
    report_request: ReportRequest,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """汇报发送结果"""
    sms_service = SmsService(db)
    log_service = LogService(db)
    
    # 验证状态值
    if report_request.status not in [TaskStatus.SUCCESS, TaskStatus.FAILED]:
        raise HTTPException(status_code=400, detail="无效的状态值")

    # 判断是否需要重试（可以根据错误信息判断）
    should_retry = False
    if report_request.status == TaskStatus.FAILED and report_request.error_message:
        # 这里可以根据错误信息判断是否需要重试
        # 例如：网络错误、临时故障等可以重试
        retryable_errors = ["网络错误", "超时", "服务暂不可用", "限流"]
        should_retry = any(error in report_request.error_message for error in retryable_errors)

    # 更新任务状态
    success = await sms_service.update_task_status(
        task_id=report_request.task_id,
        status=TaskStatus(report_request.status),
        error_message=report_request.error_message,
        should_retry=should_retry
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在或更新失败")
    
    # 记录汇报日志
    await log_service.log_report(
        task_id=report_request.task_id,
        app_id=report_request.app_id,
        status=report_request.status,
        error_message=report_request.error_message,
        request_data=report_request.model_dump()
    )
    
    return ApiResponse(message="汇报成功")
