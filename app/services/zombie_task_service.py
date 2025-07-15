from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from datetime import datetime, timedelta

from app.models.sms_task import SmsTask
from app.utils.enums import TaskStatus
from app.config import settings


class ZombieTaskService:
    """僵尸任务处理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.processing_timeout_minutes = settings.processing_timeout_minutes
        self.max_retry_count = settings.max_retry_count
    
    async def recover_zombie_tasks(self) -> int:
        """
        恢复僵尸任务（PROCESSING状态但超时未汇报的任务）
        
        Returns:
            int: 恢复的任务数量
        """
        # 计算超时阈值
        timeout_threshold = datetime.now() - timedelta(minutes=self.processing_timeout_minutes)
        
        # 查找僵尸任务
        query = select(SmsTask).where(
            and_(
                SmsTask.status == TaskStatus.PROCESSING,
                SmsTask.updated_at <= timeout_threshold
            )
        )
        
        result = await self.db.execute(query)
        zombie_tasks = result.scalars().all()
        
        if not zombie_tasks:
            return 0
        
        recovered_count = 0
        
        # 处理每个僵尸任务
        for task in zombie_tasks:
            if task.retry_count >= self.max_retry_count:
                # 超过最大重试次数，标记为最终失败
                await self._mark_final_failure(
                    task.task_id, 
                    f"处理超时，超过最大重试次数({self.max_retry_count})"
                )
            else:
                # 重置为PENDING状态，增加重试次数
                await self._reset_to_pending(task.task_id, "处理超时，自动重试")
            
            recovered_count += 1
        
        await self.db.commit()
        return recovered_count
    
    async def _mark_final_failure(self, task_id: str, result_message: str) -> None:
        """标记任务为最终失败"""
        update_query = update(SmsTask).where(
            SmsTask.task_id == task_id
        ).values(
            status=TaskStatus.FAILED,
            result=result_message,
            processing_app_id=None,
            updated_at=datetime.now(),
            reported_at=datetime.now()
        )
        
        await self.db.execute(update_query)
    
    async def _reset_to_pending(self, task_id: str, result_message: str) -> None:
        """重置任务为待处理状态"""
        # 先获取当前任务信息
        query = select(SmsTask).where(SmsTask.task_id == task_id)
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()
        
        if task:
            update_query = update(SmsTask).where(
                SmsTask.task_id == task_id
            ).values(
                status=TaskStatus.PENDING,
                retry_count=task.retry_count + 1,
                result=result_message,
                processing_app_id=None,
                updated_at=datetime.now()
            )
            
            await self.db.execute(update_query)
