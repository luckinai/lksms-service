import uuid
import urllib.parse
from datetime import datetime
from typing import Dict, Optional


def generate_task_id() -> str:
    """生成任务ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"task_{timestamp}_{unique_id}"


def generate_request_id() -> str:
    """生成请求ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"req_{timestamp}_{unique_id}"


def parse_template_params(content: str) -> Dict[str, str]:
    """
    解析模板参数
    
    Args:
        content: URL编码的参数字符串，如 "code=123456&name=张三"
        
    Returns:
        Dict[str, str]: 解析后的参数字典
    """
    try:
        # URL解码参数
        params = urllib.parse.parse_qs(content)
        # 转换为单值字典
        param_dict = {k: v[0] if v else "" for k, v in params.items()}
        return param_dict
    except Exception:
        return {}


def apply_template(template_content: str, params: Dict[str, str]) -> str:
    """
    应用模板参数
    
    Args:
        template_content: 模板内容，如 "您的验证码是{code}，用户{name}"
        params: 参数字典
        
    Returns:
        str: 替换后的内容
    """
    final_content = template_content
    for key, value in params.items():
        placeholder = f"{{{key}}}"
        final_content = final_content.replace(placeholder, str(value))
    return final_content
