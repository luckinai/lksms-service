import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.services.zombie_task_service import ZombieTaskService

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
            zombie_service = ZombieTaskService(db)

            # 恢复僵尸任务
            recovered_count = await zombie_service.recover_zombie_tasks()

            if recovered_count > 0:
                logger.info(f"恢复了 {recovered_count} 个僵尸任务")
            else:
                logger.debug("没有发现僵尸任务")

    async def manual_recover_zombie_tasks(self) -> dict:
        """手动恢复僵尸任务"""
        async with AsyncSessionLocal() as db:
            zombie_service = ZombieTaskService(db)
            recovered_count = await zombie_service.recover_zombie_tasks()

            return {
                "recovered_count": recovered_count,
                "message": f"成功恢复 {recovered_count} 个僵尸任务"
            }


# 全局调度器实例
scheduler = SchedulerService()
