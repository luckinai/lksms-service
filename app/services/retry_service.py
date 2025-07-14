from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from datetime import datetime, timedelta

from app.models.sms_task import SmsTask
from app.utils.enums import TaskStatus
from app.config import settings


class RetryService:
    """重试服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.max_retry_count = settings.max_retry_count
        self.retry_delay_minutes = settings.retry_delay_minutes
        self.processing_timeout_minutes = settings.processing_timeout_minutes
    
    async def mark_task_for_retry(self, task_id: str, error_message: str) -> bool:
        """
        标记任务需要重试
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
            
        Returns:
            bool: 是否成功标记为重试
        """
        # 获取当前任务
        query = select(SmsTask).where(SmsTask.task_id == task_id)
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            return False
        
        # 检查是否超过最大重试次数
        if task.retry_count >= self.max_retry_count:
            # 超过最大重试次数，标记为最终失败
            await self._mark_final_failure(task_id, error_message)
            return False
        
        # 增加重试次数并重置状态为PENDING
        update_query = update(SmsTask).where(
            SmsTask.task_id == task_id
        ).values(
            status=TaskStatus.PENDING,
            retry_count=task.retry_count + 1,
            processing_app_id=None,  # 清除处理APP ID
            updated_at=datetime.now()
        )
        
        await self.db.execute(update_query)
        await self.db.commit()
        
        return True
    
    async def get_retry_tasks(self, limit: int = 10) -> list:
        """
        获取需要重试的任务（延迟后的）
        
        Args:
            limit: 获取数量限制
            
        Returns:
            list: 可以重试的任务列表
        """
        # 计算重试时间阈值
        retry_threshold = datetime.now() - timedelta(minutes=self.retry_delay_minutes)
        
        query = select(SmsTask).where(
            SmsTask.status == TaskStatus.PENDING,
            SmsTask.retry_count > 0,
            SmsTask.updated_at <= retry_threshold
        ).order_by(SmsTask.retry_count, SmsTask.created_at).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _mark_final_failure(self, task_id: str, error_message: str) -> None:
        """标记任务为最终失败"""
        update_query = update(SmsTask).where(
            SmsTask.task_id == task_id
        ).values(
            status=TaskStatus.FAILED,
            updated_at=datetime.now(),
            reported_at=datetime.now()
        )
        
        await self.db.execute(update_query)
        await self.db.commit()
    
    async def recover_zombie_tasks(self) -> List[SmsTask]:
        """
        恢复僵尸任务（PROCESSING状态但超时未汇报的任务）

        Returns:
            List[SmsTask]: 恢复的僵尸任务列表
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
            return []

        # 根据重试次数决定处理方式
        for task in zombie_tasks:
            if task.retry_count >= self.max_retry_count:
                # 超过最大重试次数，标记为最终失败
                await self._mark_final_failure(task.task_id, "处理超时，超过最大重试次数")
            else:
                # 重置为PENDING状态，增加重试次数
                update_query = update(SmsTask).where(
                    SmsTask.id == task.id
                ).values(
                    status=TaskStatus.PENDING,
                    retry_count=task.retry_count + 1,
                    processing_app_id=None,  # 清除处理APP ID
                    updated_at=datetime.now()
                )
                await self.db.execute(update_query)

        await self.db.commit()
        return list(zombie_tasks)

    async def get_retry_statistics(self) -> dict:
        """获取重试统计信息"""
        # 统计各种状态的任务数量
        pending_count_query = select(SmsTask).where(SmsTask.status == TaskStatus.PENDING)
        processing_count_query = select(SmsTask).where(SmsTask.status == TaskStatus.PROCESSING)
        retry_count_query = select(SmsTask).where(SmsTask.retry_count > 0)

        pending_result = await self.db.execute(pending_count_query)
        processing_result = await self.db.execute(processing_count_query)
        retry_result = await self.db.execute(retry_count_query)

        return {
            "pending_tasks": len(pending_result.scalars().all()),
            "processing_tasks": len(processing_result.scalars().all()),
            "retry_tasks": len(retry_result.scalars().all()),
            "max_retry_count": self.max_retry_count,
            "retry_delay_minutes": self.retry_delay_minutes,
            "processing_timeout_minutes": self.processing_timeout_minutes
        }
