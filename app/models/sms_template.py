from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.database import Base


class SmsTemplate(Base):
    """短信模板表"""
    __tablename__ = "sms_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False, comment="模板名称")
    template_content = Column(String(200), nullable=False, comment="模板内容，支持{param}占位符")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<SmsTemplate(id={self.id}, name='{self.template_name}', active={self.is_active})>"
