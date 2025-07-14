from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from datetime import datetime

from app.models.sms_task import SmsTask
from app.models.default_sms import DefaultSmsData
from app.utils.enums import TaskStatus
from app.utils.helpers import generate_task_id
from app.services.template_service import TemplateService


class SmsService:
    """短信服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.template_service = TemplateService(db)
    
    async def create_task(
        self,
        phone_number: str,
        content: Optional[str],
        use_template: bool = False,
        source: Optional[str] = None
    ) -> SmsTask:
        """
        创建发送任务
        
        Args:
            phone_number: 手机号码
            content: 发送内容（可为空）
            use_template: 是否使用模板
            source: 来源标识
            
        Returns:
            Tuple[SmsTask, str]: (任务对象, 最终内容)
            
        Raises:
            ValueError: 当默认内容已发送或其他业务错误时
        """
        final_content = content
        
        # 如果内容为空，获取默认内容
        if not content:
            default_data = await self._get_default_content(phone_number)
            if not default_data:
                raise ValueError("未找到该手机号的默认内容")
            
            if default_data.is_sent:
                raise ValueError("该手机号的默认内容已发送过")
            
            final_content = default_data.content
            use_template = default_data.use_template
            
            # 标记为已发送
            await self._mark_default_sent(phone_number)
        
        # 如果使用模板，处理模板内容
        if use_template and final_content:
            processed_content = await self.template_service.process_template_content(final_content)
            if processed_content:
                final_content = processed_content
        
        # 创建任务
        task_id = generate_task_id()
        task = SmsTask(
            task_id=task_id,
            phone_number=phone_number,
            content=final_content,
            status=TaskStatus.PENDING,
            source=source
        )
        
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        return task
    
    async def get_task_by_id(self, task_id: str) -> Optional[SmsTask]:
        """根据任务ID获取任务"""
        query = select(SmsTask).where(SmsTask.task_id == task_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_pending_tasks_safely(self, app_id: str, limit: int = 10) -> List[SmsTask]:
        """
        安全地获取待处理任务（并发控制）
        
        Args:
            app_id: APP标识
            limit: 获取数量限制
            
        Returns:
            List[SmsTask]: 获取到的任务列表
        """
        async with self.db.begin():
            # 使用FOR UPDATE SKIP LOCKED确保并发安全
            query = select(SmsTask).where(
                SmsTask.status == TaskStatus.PENDING
            ).order_by(SmsTask.created_at).limit(limit).with_for_update(skip_locked=True)
            
            result = await self.db.execute(query)
            tasks = result.scalars().all()
            
            if tasks:
                # 原子性更新状态
                task_ids = [task.id for task in tasks]
                update_query = update(SmsTask).where(
                    SmsTask.id.in_(task_ids)
                ).values(
                    status=TaskStatus.PROCESSING,
                    processing_app_id=app_id,
                    updated_at=datetime.now()
                )
                await self.db.execute(update_query)
        
        return list(tasks)
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        error_message: Optional[str] = None,
        should_retry: bool = False
    ) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息（失败时）
            should_retry: 是否应该重试（失败时）

        Returns:
            bool: 是否更新成功
        """
        # 如果是失败状态且需要重试，则使用重试服务处理
        if status == TaskStatus.FAILED and should_retry:
            from app.services.retry_service import RetryService
            retry_service = RetryService(self.db)
            return await retry_service.mark_task_for_retry(task_id, error_message or "")

        update_data = {
            "status": status,
            "updated_at": datetime.now()
        }

        if status == TaskStatus.SUCCESS:
            update_data["sent_at"] = datetime.now()
        elif status == TaskStatus.FAILED:
            # 最终失败，清除处理APP ID
            update_data["processing_app_id"] = None

        update_data["reported_at"] = datetime.now()

        query = update(SmsTask).where(
            SmsTask.task_id == task_id
        ).values(**update_data)

        result = await self.db.execute(query)
        await self.db.commit()

        return result.rowcount > 0
    
    async def _get_default_content(self, phone_number: str) -> Optional[DefaultSmsData]:
        """获取默认内容"""
        query = select(DefaultSmsData).where(
            DefaultSmsData.phone_number == phone_number
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _mark_default_sent(self, phone_number: str) -> None:
        """标记默认内容为已发送"""
        query = update(DefaultSmsData).where(
            DefaultSmsData.phone_number == phone_number
        ).values(
            is_sent=True,
            updated_at=datetime.now()
        )
        await self.db.execute(query)
    
    async def create_default_sms(
        self,
        phone_number: str,
        content: str,
        use_template: bool = False
    ) -> DefaultSmsData:
        """创建默认短信内容"""
        default_sms = DefaultSmsData(
            phone_number=phone_number,
            content=content,
            use_template=use_template
        )
        
        self.db.add(default_sms)
        await self.db.commit()
        await self.db.refresh(default_sms)
        
        return default_sms
