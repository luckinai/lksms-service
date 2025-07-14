import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.services.retry_service import RetryService

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务服务"""
    
    def __init__(self):
        self.is_running = False
        self.check_interval = 300  # 5分钟检查一次
    
    async def start_zombie_task_recovery(self):
        """启动僵尸任务恢复定时器"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("启动僵尸任务恢复定时器")
        
        while self.is_running:
            try:
                await self._recover_zombie_tasks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"僵尸任务恢复出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再重试
    
    async def stop_zombie_task_recovery(self):
        """停止僵尸任务恢复定时器"""
        self.is_running = False
        logger.info("停止僵尸任务恢复定时器")
    
    async def _recover_zombie_tasks(self):
        """恢复僵尸任务"""
        async with AsyncSessionLocal() as db:
            retry_service = RetryService(db)
            
            # 恢复僵尸任务
            zombie_tasks = await retry_service.recover_zombie_tasks()
            
            if zombie_tasks:
                logger.info(f"恢复了 {len(zombie_tasks)} 个僵尸任务")
                for task in zombie_tasks:
                    logger.info(f"恢复任务: {task.task_id}, 重试次数: {task.retry_count}")
            else:
                logger.debug("没有发现僵尸任务")
    
    async def manual_recover_zombie_tasks(self) -> dict:
        """手动恢复僵尸任务"""
        async with AsyncSessionLocal() as db:
            retry_service = RetryService(db)
            zombie_tasks = await retry_service.recover_zombie_tasks()
            
            return {
                "recovered_count": len(zombie_tasks),
                "recovered_tasks": [
                    {
                        "task_id": task.task_id,
                        "phone_number": task.phone_number,
                        "retry_count": task.retry_count,
                        "processing_app_id": task.processing_app_id
                    }
                    for task in zombie_tasks
                ]
            }


# 全局调度器实例
scheduler = SchedulerService()
