from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class SmsTask(Base):
    """发送任务表"""
    __tablename__ = "sms_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, nullable=False, comment="任务ID")
    phone_number = Column(String(20), nullable=False, index=True, comment="手机号码")
    content = Column(String(200), nullable=False, comment="发送内容")
    status = Column(Integer, default=0, index=True, comment="任务状态: 0=PENDING, 1=PROCESSING, 2=SUCCESS, 3=FAILED")
    source = Column(String(50), comment="来源标识")
    retry_count = Column(Integer, default=0, comment="重试次数")
    processing_app_id = Column(String(50), index=True, comment="处理中的APP ID")
    result = Column(String(500), comment="最后一次发送汇报结果，失败时记录失败原因")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    sent_at = Column(DateTime(timezone=True), comment="发送时间")
    reported_at = Column(DateTime(timezone=True), comment="汇报时间")
    
    def __repr__(self):
        return f"<SmsTask(id={self.id}, task_id='{self.task_id}', status={self.status})>"
