#!/bin/bash

# LKSMS数据库恢复脚本

if [ $# -eq 0 ]; then
    echo "用法: $0 <备份文件路径>"
    echo "示例: $0 ./backups/lksms_backup_20231201_120000.sql.gz"
    exit 1
fi

BACKUP_FILE=$1

# 检查备份文件是否存在
if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

echo "准备恢复数据库..."
echo "备份文件: $BACKUP_FILE"
read -p "确认要恢复吗？这将覆盖现有数据 (y/N): " confirm

if [[ $confirm != [yY] ]]; then
    echo "恢复已取消"
    exit 0
fi

# 停止应用服务（保留数据库服务）
echo "停止应用服务..."
docker-compose stop lksms-service

# 解压备份文件（如果是压缩的）
if [[ $BACKUP_FILE == *.gz ]]; then
    echo "解压备份文件..."
    TEMP_FILE="/tmp/restore_$(date +%s).sql"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    RESTORE_FILE="$TEMP_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# 执行恢复
echo "开始恢复数据库..."
docker-compose exec -T postgres psql -U lksms_user -d lksms_db < "$RESTORE_FILE"

if [ $? -eq 0 ]; then
    echo "恢复成功！"
    
    # 清理临时文件
    if [[ -n "$TEMP_FILE" && -f "$TEMP_FILE" ]]; then
        rm "$TEMP_FILE"
    fi
    
    # 重启应用服务
    echo "重启应用服务..."
    docker-compose up -d lksms-service
    
    echo "恢复完成！"
else
    echo "恢复失败！"
    exit 1
fi
