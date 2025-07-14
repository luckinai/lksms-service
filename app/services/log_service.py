from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.logs import ReceiveLog, SendLog, ReportLog


class LogService:
    """日志服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_receive(
        self,
        request_id: str,
        phone_number: str,
        content: Optional[str],
        use_template: bool,
        source_ip: str,
        user_agent: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        status_code: int
    ) -> ReceiveLog:
        """记录接收日志"""
        log = ReceiveLog(
            request_id=request_id,
            phone_number=phone_number,
            content=content,
            use_template=use_template,
            source_ip=source_ip,
            user_agent=user_agent,
            request_data=request_data,
            response_data=response_data,
            status_code=status_code
        )
        
        self.db.add(log)
        await self.db.commit()
        return log
    
    async def log_send(
        self,
        task_id: str,
        app_id: str,
        phone_number: str,
        content: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any]
    ) -> SendLog:
        """记录发送日志"""
        log = SendLog(
            task_id=task_id,
            app_id=app_id,
            phone_number=phone_number,
            content=content,
            request_data=request_data,
            response_data=response_data
        )
        
        self.db.add(log)
        await self.db.commit()
        return log
    
    async def log_report(
        self,
        task_id: str,
        app_id: str,
        status: int,
        error_message: Optional[str],
        request_data: Dict[str, Any]
    ) -> ReportLog:
        """记录汇报日志"""
        log = ReportLog(
            task_id=task_id,
            app_id=app_id,
            status=status,
            error_message=error_message,
            request_data=request_data
        )
        
        self.db.add(log)
        await self.db.commit()
        return log
