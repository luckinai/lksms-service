#!/bin/bash

# LKSMS数据库密码修改脚本

set -e

echo "🔐 LKSMS数据库密码修改工具"
echo "================================"

# 检查参数
if [ $# -ne 1 ]; then
    echo "用法: $0 <新密码>"
    echo "示例: $0 'new_secure_password_123'"
    exit 1
fi

NEW_PASSWORD="$1"
OLD_PASSWORD="lksms_password"  # 当前密码
DB_USER="lksms_user"
DB_NAME="lksms_db"

# 验证新密码强度
if [ ${#NEW_PASSWORD} -lt 8 ]; then
    echo "❌ 错误: 密码长度至少8位"
    exit 1
fi

echo "新密码: ${NEW_PASSWORD:0:3}***"
echo ""

# 确认操作
read -p "⚠️  确认要修改数据库密码吗? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "操作已取消"
    exit 0
fi

# 1. 检查服务状态
echo "📊 检查服务状态..."
if ! docker-compose ps postgres | grep -q "Up"; then
    echo "❌ PostgreSQL服务未运行，请先启动服务"
    exit 1
fi

# 2. 备份数据库
echo "💾 备份数据库..."
BACKUP_FILE="./backups/before_password_change_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p ./backups
docker-compose exec -T postgres pg_dump -U $DB_USER $DB_NAME > "$BACKUP_FILE"
echo "✅ 备份完成: $BACKUP_FILE"

# 3. 修改数据库内部用户密码
echo "🔄 修改数据库用户密码..."
docker-compose exec postgres psql -U $DB_USER -d $DB_NAME -c "ALTER USER $DB_USER WITH PASSWORD '$NEW_PASSWORD';"

if [ $? -eq 0 ]; then
    echo "✅ 数据库用户密码修改成功"
else
    echo "❌ 数据库用户密码修改失败"
    exit 1
fi

# 4. 更新docker-compose.yml
echo "📝 更新docker-compose.yml..."
sed -i.bak "s/POSTGRES_PASSWORD: $OLD_PASSWORD/POSTGRES_PASSWORD: $NEW_PASSWORD/g" docker-compose.yml
sed -i.bak "s|postgresql+asyncpg://lksms_user:$OLD_PASSWORD@|postgresql+asyncpg://lksms_user:$NEW_PASSWORD@|g" docker-compose.yml

echo "✅ docker-compose.yml已更新"

# 5. 更新.env文件（如果存在）
if [ -f .env ]; then
    echo "📝 更新.env文件..."
    sed -i.bak "s|postgresql+asyncpg://lksms_user:$OLD_PASSWORD@|postgresql+asyncpg://lksms_user:$NEW_PASSWORD@|g" .env
    echo "✅ .env文件已更新"
fi

# 6. 重启应用服务以使用新密码
echo "🔄 重启应用服务..."
docker-compose restart lksms-service

# 7. 等待服务启动并测试连接
echo "⏳ 等待服务启动..."
sleep 10

# 8. 健康检查
echo "🏥 执行健康检查..."
max_attempts=10
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 服务健康检查通过！"
        break
    else
        echo "⏳ 等待服务启动... ($attempt/$max_attempts)"
        sleep 3
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ 服务启动失败，可能是密码配置问题"
    echo "📋 查看服务日志:"
    docker-compose logs --tail=20 lksms-service
    echo ""
    echo "🔧 如需回滚，请运行:"
    echo "   mv docker-compose.yml.bak docker-compose.yml"
    if [ -f .env.bak ]; then
        echo "   mv .env.bak .env"
    fi
    echo "   docker-compose restart lksms-service"
    exit 1
fi

# 9. 清理备份文件
rm -f docker-compose.yml.bak
if [ -f .env.bak ]; then
    rm -f .env.bak
fi

echo ""
echo "🎉 数据库密码修改完成！"
echo "📋 修改摘要:"
echo "   - 数据库用户密码已更新"
echo "   - docker-compose.yml已更新"
if [ -f .env ]; then
    echo "   - .env文件已更新"
fi
echo "   - 应用服务已重启"
echo "   - 数据备份: $BACKUP_FILE"
echo ""
echo "⚠️  重要提醒:"
echo "   1. 请更新其他可能使用旧密码的配置文件"
echo "   2. 如果有外部应用连接此数据库，请同步更新密码"
echo "   3. 建议提交配置文件更改到版本控制"
