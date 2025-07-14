#!/bin/bash

# LKSMS数据库备份脚本

# 配置
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="lksms_backup_${DATE}.sql"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
echo "开始备份数据库..."
docker-compose exec -T postgres pg_dump -U lksms_user lksms_db > "${BACKUP_DIR}/${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo "备份成功: ${BACKUP_DIR}/${BACKUP_FILE}"
    
    # 压缩备份文件
    gzip "${BACKUP_DIR}/${BACKUP_FILE}"
    echo "备份已压缩: ${BACKUP_DIR}/${BACKUP_FILE}.gz"
    
    # 删除7天前的备份（可选）
    find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
    echo "已清理7天前的旧备份"
else
    echo "备份失败！"
    exit 1
fi
