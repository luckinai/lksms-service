from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.database import Base


class DefaultSmsData(Base):
    """默认短信数据信息表"""
    __tablename__ = "default_sms_data"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False, unique=True, index=True, comment="手机号码")
    content = Column(String(200), nullable=False, comment="默认发送内容")
    use_template = Column(Boolean, default=False, comment="是否使用模板")
    is_sent = Column(Boolean, default=False, index=True, comment="是否已发送")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<DefaultSmsData(id={self.id}, phone='{self.phone_number}', sent={self.is_sent})>"
