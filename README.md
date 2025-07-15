# LKSMS Service - 短信发送任务服务

一个基于FastAPI的短信发送任务服务，通过WebAPI方式为第三方系统提供短信发送功能。系统采用任务队列模式，支持第三方系统提交发送任务，短信发送APP轮询获取任务并汇报发送结果。

## 🚀 功能特性

- **任务队列模式**: 第三方系统提交任务，APP轮询获取
- **模板功能**: 支持参数化短信内容生成
- **智能任务调度**: 新任务优先，重试任务次之
- **并发安全**: 多APP获取任务时避免重复
- **自动故障恢复**: 定时检测并恢复僵尸任务
- **APP主导重试**: 由APP判断是否需要重试，提高灵活性
- **Basic Auth认证**: 简单有效的API认证方式
- **完整日志**: 接收、发送、汇报全流程日志记录
- **默认内容**: 支持预设默认短信内容，每个号码只发送一次
- **高效统计**: 使用数据库聚合查询，性能优异

## 🛠 技术栈

- **后端框架**: FastAPI (Python)
- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy (异步)
- **认证方式**: HTTP Basic Auth
- **容器化**: Docker + Docker Compose

## 📋 系统要求

- Python 3.11+
- PostgreSQL 12+
- Docker & Docker Compose (可选)

## 🔧 快速开始

### 方式一：Docker Compose (推荐)

1. **克隆项目**
```bash
git clone <repository-url>
cd lksms-service
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，修改认证密码等配置
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **验证服务**
```bash
curl http://localhost:8000/health
```

### 方式二：本地开发

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置数据库**
```bash
# 创建PostgreSQL数据库
createdb lksms_db

# 执行数据库迁移
psql -d lksms_db -f migrations/001_initial_schema.sql
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件
```

4. **启动服务**
```bash
python -m app.main
# 或者
uvicorn app.main:app --reload
```

## 📚 API文档

服务启动后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 认证方式

所有API接口均需要HTTP Basic Auth认证：
```bash
curl -u admin:your_password http://localhost:8000/api/v1/sms/...
```

### 主要接口

#### 1. 提交短信发送任务
```bash
POST /api/v1/sms/send
Content-Type: application/json
Authorization: Basic <base64(username:password)>

{
    "phone_number": "13800138000",
    "content": "code=123456&name=张三",
    "use_template": true,
    "source": "system_a"
}
```

#### 2. 查询任务状态
```bash
GET /api/v1/sms/task/{task_id}
Authorization: Basic <base64(username:password)>
```

#### 3. 获取待发送任务（APP使用）
```bash
GET /api/v1/sms/tasks/pending?app_id=sms_app_001&limit=10
Authorization: Basic <base64(username:password)>
```

#### 4. 汇报发送结果（APP使用）
```bash
POST /api/v1/sms/report
Content-Type: application/json
Authorization: Basic <base64(username:password)>

{
    "task_id": "task_20231201_001",
    "app_id": "sms_app_001",
    "status": 2,
    "error_message": "",
    "should_retry": false
}
```

## 🎯 业务流程

### 短信发送流程

1. **第三方系统**调用`/api/v1/sms/send`提交发送请求
2. **系统处理**：
   - 如果content为空，查询默认内容
   - 如果use_template=true，进行模板处理
   - 创建发送任务，记录到result字段
3. **智能任务调度**：
   - 优先分配新任务（retry_count=0）
   - 无新任务时分配重试任务（retry_count>0）
4. **短信APP**定时调用`/api/v1/sms/tasks/pending`获取任务
5. **APP发送短信**后调用`/api/v1/sms/report`汇报结果
   - APP判断是否需要重试（should_retry字段）
   - 系统根据APP判断决定重试或标记失败
6. **自动故障恢复**：
   - 定时检测僵尸任务（PROCESSING状态超时）
   - 自动重试或标记为最终失败
7. **系统记录**完整的操作日志和结果信息

### 模板处理示例

```
输入内容: "code=123456&name=张三"
模板内容: "您的验证码是{code}，用户{name}"
最终结果: "您的验证码是123456，用户张三"
```

### 状态说明

- `0` - PENDING: 待处理
- `1` - PROCESSING: 处理中
- `2` - SUCCESS: 成功
- `3` - FAILED: 失败

### 任务调度策略

系统采用智能任务调度策略，确保高效处理：

1. **优先级排序**：
   - 新任务（retry_count=0）优先处理
   - 重试任务（retry_count>0）按重试次数和创建时间排序

2. **重试间隔控制**：
   - 重试任务需要等待配置的间隔时间（默认5分钟）
   - 避免频繁重试同一任务，给外部系统恢复时间

3. **并发控制**：
   - 使用数据库行锁（FOR UPDATE SKIP LOCKED）
   - 防止多个APP获取相同任务

4. **自动恢复**：
   - 每5分钟检测僵尸任务
   - 超时任务自动重试或标记失败

## 🔒 并发控制

系统使用数据库行锁确保多个APP获取任务时的并发安全：

```sql
SELECT * FROM sms_tasks 
WHERE status = 0 
ORDER BY created_at 
LIMIT 10 
FOR UPDATE SKIP LOCKED;
```

## 📊 数据库结构

### 核心表

- `sms_templates` - 短信模板表
- `sms_tasks` - 发送任务表（新增result字段记录发送结果）
- `default_sms_data` - 默认短信数据表
- `receive_logs` - 接收日志表
- `send_logs` - 发送日志表
- `report_logs` - 汇报日志表

### 重要字段说明

#### sms_tasks表关键字段：
- `retry_count`: 重试次数，用于任务优先级排序
- `result`: 最后一次发送汇报结果，失败时记录失败原因
- `processing_app_id`: 处理中的APP ID，用于并发控制
- `status`: 任务状态（0=PENDING, 1=PROCESSING, 2=SUCCESS, 3=FAILED）

详细结构请查看 `migrations/001_initial_schema.sql`

## 🧪 测试

测试脚本位于 `test_script/` 目录：

```bash
# 运行API测试（包含新功能测试）
python test_script/test_api.py
```

### 测试覆盖的新功能：
- 任务优先级调度测试
- APP主导重试机制测试
- 重试间隔控制测试
- 僵尸任务恢复测试
- 高效统计查询测试

## 📝 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| **认证配置** | | |
| BASIC_AUTH_USERNAME | Basic Auth用户名 | admin |
| BASIC_AUTH_PASSWORD | Basic Auth密码 | your_secure_password |
| **数据库配置** | | |
| POSTGRES_HOST | 数据库主机 | postgres (Docker内部) |
| POSTGRES_PORT | 数据库端口 | 5432 |
| POSTGRES_DB | 数据库名称 | lksms_db |
| POSTGRES_USER | 数据库用户名 | lksms_user |
| POSTGRES_PASSWORD | 数据库密码 | lksms_password |
| **应用配置** | | |
| APP_HOST | 服务监听地址 | 0.0.0.0 |
| APP_PORT | 服务监听端口 | 8000 |
| DEBUG | 调试模式 | false |
| LOG_LEVEL | 日志级别 | INFO |
| **重试配置** | | |
| MAX_RETRY_COUNT | 最大重试次数 | 3 |
| RETRY_DELAY_MINUTES | 重试间隔时间(分钟) | 5 |
| PROCESSING_TIMEOUT_MINUTES | 处理超时(分钟) | 30 |
| **文档配置** | | |
| ENABLE_DOCS | 启用API文档 | true |

> **注意**: DATABASE_URL由应用根据数据库参数自动拼接，无需手动配置

## 🚀 部署和更新

### 数据持久化说明

**重要**：使用`docker-compose down`不会删除数据库数据！

- ✅ `docker-compose down` - 安全，保留数据
- ❌ `docker-compose down -v` - 危险，会删除所有数据
- ❌ `docker-compose down --volumes` - 危险，会删除所有数据

数据存储在命名卷`postgres_data`中，只有明确使用`-v`或`--volumes`参数才会删除。

### 更新部署流程

#### 方法一：使用自动化脚本（推荐）

```bash
# 给脚本添加执行权限（首次）
chmod +x scripts/*.sh

# 自动化部署（包含备份、更新、健康检查）
./scripts/deploy.sh
```

#### 方法二：手动更新

```bash
# 1. 获取最新代码
git pull origin main

# 2. 备份数据库（推荐）
./scripts/backup.sh

# 3. 停止服务（保留数据）
docker-compose down

# 4. 重新构建并启动
docker-compose up -d --build

# 5. 验证服务
curl http://localhost:8000/health
```

#### 方法三：零停机更新

```bash
# 获取最新代码
git pull origin main

# 滚动更新（不停机）
docker-compose up -d --build
```

### 数据备份和恢复

#### 备份数据库

```bash
# 手动备份
./scripts/backup.sh

# 或者直接使用docker命令
docker-compose exec postgres pg_dump -U lksms_user lksms_db > backup.sql
```

#### 恢复数据库

```bash
# 从备份恢复
./scripts/restore.sh ./backups/lksms_backup_20231201_120000.sql.gz

# 或者直接使用docker命令
docker-compose exec -T postgres psql -U lksms_user -d lksms_db < backup.sql
```

### 定时备份设置

```bash
# 编辑crontab
crontab -e

# 添加定时备份任务（每天凌晨2点备份）
0 2 * * * cd /path/to/lksms-service && ./scripts/backup.sh >> /var/log/lksms-backup.log 2>&1
```

### 生产环境建议

1. **修改默认密码**：更改Basic Auth密码
2. **定期备份**：设置cron定时备份（见上方示例）
3. **监控告警**：添加日志监控和性能监控
4. **负载均衡**：多实例部署时使用负载均衡
5. **SSL证书**：使用HTTPS加密通信
6. **资源限制**：在docker-compose.yml中设置内存和CPU限制

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📞 支持

如有问题，请提交Issue或联系开发团队。

## 📝 免责声明

本项目仅供个人学习交流研究，非商用，禁止商业用途和倒卖，不承担用户使用资源对自己或他人造成的任何影响和伤害。