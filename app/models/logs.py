from sqlalchemy import Column, Integer, String, DateTime, func, JSON, Boolean
from app.database import Base


class ReceiveLog(Base):
    """接收日志表"""
    __tablename__ = "receive_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(50), comment="请求ID")
    phone_number = Column(String(20), comment="手机号码")
    content = Column(String(200), comment="发送内容")
    use_template = Column(Boolean, comment="是否使用模板")
    source_ip = Column(String(45), comment="来源IP")
    user_agent = Column(String(500), comment="用户代理")
    request_data = Column(JSON, comment="完整请求数据")
    response_data = Column(JSON, comment="响应数据")
    status_code = Column(Integer, comment="响应状态码")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="创建时间")


class SendLog(Base):
    """发送日志表"""
    __tablename__ = "send_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), index=True, comment="任务ID")
    app_id = Column(String(50), comment="APP标识")
    phone_number = Column(String(20), comment="手机号码")
    content = Column(String(200), comment="发送内容")
    request_data = Column(JSON, comment="请求数据")
    response_data = Column(JSON, comment="响应数据")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")


class ReportLog(Base):
    """汇报日志表"""
    __tablename__ = "report_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), index=True, comment="任务ID")
    app_id = Column(String(50), comment="APP标识")
    status = Column(Integer, comment="发送状态: 2=SUCCESS, 3=FAILED")
    error_message = Column(String(500), comment="错误信息")
    request_data = Column(JSON, comment="汇报数据")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
