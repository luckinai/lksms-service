#!/bin/bash

# LKSMS自动化部署脚本

set -e  # 遇到错误立即退出

echo "🚀 开始LKSMS服务部署..."

# 1. 检查Git状态
echo "📋 检查Git状态..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  警告: 工作目录有未提交的更改"
    read -p "是否继续部署? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "部署已取消"
        exit 0
    fi
fi

# 2. 获取最新代码
echo "📥 获取最新代码..."
git pull origin main

# 3. 备份数据库（可选）
read -p "是否要备份数据库? (Y/n): " backup_confirm
if [[ $backup_confirm != [nN] ]]; then
    echo "💾 备份数据库..."
    ./scripts/backup.sh
fi

# 4. 检查服务状态
echo "🔍 检查当前服务状态..."
if docker-compose ps | grep -q "Up"; then
    echo "📊 当前服务正在运行，准备更新..."
    RESTART_NEEDED=true
else
    echo "📊 服务未运行，将进行首次启动..."
    RESTART_NEEDED=false
fi

# 5. 构建新镜像
echo "🔨 构建新镜像..."
docker-compose build --no-cache lksms-service

# 6. 更新服务
if [ "$RESTART_NEEDED" = true ]; then
    echo "🔄 滚动更新服务..."
    docker-compose up -d --no-deps lksms-service
else
    echo "🆕 启动服务..."
    docker-compose up -d
fi

# 7. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 8. 健康检查
echo "🏥 执行健康检查..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 服务健康检查通过！"
        break
    else
        echo "⏳ 等待服务启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ 服务启动失败，查看日志:"
    docker-compose logs --tail=50 lksms-service
    exit 1
fi

# 9. 清理旧镜像
echo "🧹 清理旧镜像..."
docker image prune -f

# 10. 显示服务状态
echo "📊 当前服务状态:"
docker-compose ps

echo "🎉 部署完成！"
echo "📚 API文档: http://localhost:8000/docs"
echo "🏥 健康检查: http://localhost:8000/health"
