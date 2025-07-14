from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.sms_template import SmsTemplate
from app.utils.helpers import parse_template_params, apply_template


class TemplateService:
    """模板服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_active_template(self) -> Optional[SmsTemplate]:
        """
        获取第一个可用的模板
        
        Returns:
            Optional[SmsTemplate]: 可用的模板，如果没有则返回None
        """
        query = select(SmsTemplate).where(
            SmsTemplate.is_active == True
        ).order_by(SmsTemplate.id).limit(1)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def process_template_content(self, content: str) -> Optional[str]:
        """
        处理模板内容
        
        Args:
            content: URL编码的参数字符串
            
        Returns:
            Optional[str]: 处理后的内容，如果没有可用模板则返回None
        """
        # 获取可用模板
        template = await self.get_active_template()
        if not template:
            return None
        
        # 解析参数
        params = parse_template_params(content)
        
        # 应用模板
        final_content = apply_template(template.template_content, params)
        return final_content
    
    async def create_template(self, template_name: str, template_content: str) -> SmsTemplate:
        """
        创建新模板
        
        Args:
            template_name: 模板名称
            template_content: 模板内容
            
        Returns:
            SmsTemplate: 创建的模板
        """
        template = SmsTemplate(
            template_name=template_name,
            template_content=template_content,
            is_active=True
        )
        
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        
        return template
