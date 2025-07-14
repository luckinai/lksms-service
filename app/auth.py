from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from app.config import settings

# 创建HTTP Basic认证实例
security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    验证Basic Auth凭据
    
    Args:
        credentials: HTTP Basic认证凭据
        
    Returns:
        str: 验证通过的用户名
        
    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    # 使用secrets.compare_digest防止时序攻击
    correct_username = secrets.compare_digest(
        credentials.username, 
        settings.basic_auth_username
    )
    correct_password = secrets.compare_digest(
        credentials.password, 
        settings.basic_auth_password
    )
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username
