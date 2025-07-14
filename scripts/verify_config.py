#!/usr/bin/env python3
"""
配置验证脚本
验证新的环境变量配置是否正确
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings


def main():
    print("🔍 LKSMS配置验证")
    print("=" * 50)
    
    # 验证数据库配置
    print("\n📊 数据库配置:")
    print(f"   主机: {settings.postgres_host}")
    print(f"   端口: {settings.postgres_port}")
    print(f"   数据库: {settings.postgres_db}")
    print(f"   用户: {settings.postgres_user}")
    print(f"   密码: {'*' * len(settings.postgres_password)}")
    
    # 显示拼接的DATABASE_URL
    print(f"\n🔗 拼接的DATABASE_URL:")
    print(f"   {settings.database_url}")
    
    # 验证应用配置
    print(f"\n⚙️  应用配置:")
    print(f"   监听地址: {settings.app_host}:{settings.app_port}")
    print(f"   调试模式: {settings.debug}")
    print(f"   日志级别: {settings.log_level}")
    print(f"   启用文档: {settings.enable_docs}")
    
    # 验证认证配置
    print(f"\n🔐 认证配置:")
    print(f"   用户名: {settings.basic_auth_username}")
    print(f"   密码: {'*' * len(settings.basic_auth_password)}")
    
    # 验证重试配置
    print(f"\n🔄 重试配置:")
    print(f"   最大重试次数: {settings.max_retry_count}")
    print(f"   重试延迟: {settings.retry_delay_minutes}分钟")
    print(f"   处理超时: {settings.processing_timeout_minutes}分钟")
    
    # 检查环境变量文件
    print(f"\n📁 配置文件检查:")
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if env_file.exists():
        print(f"   ✅ .env文件存在")
    else:
        print(f"   ❌ .env文件不存在")
        print(f"   💡 建议: cp .env.example .env")
    
    if env_example.exists():
        print(f"   ✅ .env.example文件存在")
    else:
        print(f"   ❌ .env.example文件不存在")
    
    # 检查Docker配置
    docker_compose = project_root / "docker-compose.yml"
    if docker_compose.exists():
        print(f"   ✅ docker-compose.yml文件存在")
    else:
        print(f"   ❌ docker-compose.yml文件不存在")
    
    # 验证配置一致性
    print(f"\n🔍 配置一致性检查:")
    
    # 检查是否有遗留的DATABASE_URL环境变量
    if "DATABASE_URL" in os.environ:
        print(f"   ⚠️  检测到DATABASE_URL环境变量，现在由应用自动拼接")
        print(f"   💡 建议: 从.env文件中移除DATABASE_URL配置")
    else:
        print(f"   ✅ 没有冲突的DATABASE_URL环境变量")
    
    # 检查必要的环境变量
    required_vars = [
        "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", 
        "POSTGRES_USER", "POSTGRES_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not hasattr(settings, var.lower()) or not getattr(settings, var.lower()):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"   ❌ 缺少必要配置: {', '.join(missing_vars)}")
    else:
        print(f"   ✅ 所有必要的数据库配置都已设置")
    
    print(f"\n🎉 配置验证完成!")
    
    if missing_vars:
        print(f"\n⚠️  发现问题，请检查配置文件")
        return 1
    else:
        print(f"\n✅ 配置看起来正常!")
        return 0


if __name__ == "__main__":
    exit(main())
