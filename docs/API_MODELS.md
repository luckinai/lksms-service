# API响应模型文档

本文档详细说明了LKSMS服务所有API接口的响应模型，便于前端开发和代码生成工具使用。

## 📋 通用响应格式

所有API接口都使用统一的响应格式：

```typescript
interface ApiResponse<T> {
  code: number;        // 响应状态码，200表示成功
  message: string;     // 响应消息
  data?: T;           // 响应数据，具体类型见下文
}
```

## 🔧 短信服务接口模型

### 1. 发送短信响应 - SmsResponse

**接口**: `POST /api/v1/sms/send`

```typescript
interface SmsResponse {
  task_id: string;      // 任务ID
  status: number;       // 任务状态码
  final_content: string; // 最终发送内容
}
```

### 2. 任务查询响应 - TaskQueryResponse

**接口**: `GET /api/v1/sms/task/{task_id}`

```typescript
interface TaskQueryResponse {
  task_id: string;           // 任务ID
  phone_number: string;      // 手机号码
  content: string;           // 发送内容
  status: number;            // 任务状态
  created_at: string;        // 创建时间 (ISO格式)
  sent_at?: string;          // 发送时间 (ISO格式，可选)
}
```

### 3. 待处理任务响应 - PendingTasksResponse

**接口**: `GET /api/v1/sms/tasks/pending`

```typescript
interface PendingTaskResponse {
  task_id: string;      // 任务ID
  phone_number: string; // 手机号码
  content: string;      // 发送内容
}

interface PendingTasksResponse {
  total_count: number;           // 获取到的任务总数
  app_id: string;               // 请求的APP ID
  tasks: PendingTaskResponse[]; // 任务列表
}
```

### 4. 发送结果汇报请求 - ReportRequest

**接口**: `POST /api/v1/sms/report`

```typescript
interface ReportRequest {
  task_id: string;          // 任务ID
  app_id: string;           // APP标识
  status: number;           // 发送状态: 2=SUCCESS, 3=FAILED
  error_message?: string;   // 错误信息（失败时）
  should_retry: boolean;    // 是否应该重试（由APP判断）
}
```

## 🛠 管理接口模型

### 1. 模板响应 - TemplateResponse

**接口**: `POST /api/v1/admin/template`

```typescript
interface TemplateResponse {
  id: number;              // 模板ID
  template_name: string;   // 模板名称
  template_content: string; // 模板内容
  is_active: boolean;      // 是否启用
}
```

### 2. 默认短信响应 - DefaultSmsResponse

**接口**: `POST /api/v1/admin/default-sms`

```typescript
interface DefaultSmsResponse {
  id: number;           // 记录ID
  phone_number: string; // 手机号码
  content: string;      // 默认发送内容
  use_template: boolean; // 是否使用模板
  is_sent: boolean;     // 是否已发送
}
```

### 3. 僵尸任务恢复响应 - ZombieTaskRecoveryResponse

**接口**: `POST /api/v1/admin/recover-zombie-tasks`

```typescript
interface RecoveredTaskInfo {
  task_id: string;           // 任务ID
  phone_number: string;      // 手机号码
  retry_count: number;       // 重试次数
  processing_app_id?: string; // 处理中的APP ID
}

interface ZombieTaskRecoveryResponse {
  recovered_count: number;           // 恢复的任务数量
  recovered_tasks: RecoveredTaskInfo[]; // 恢复的任务列表
}
```

### 4. 任务统计响应 - TaskStatisticsResponse

**接口**: `GET /api/v1/admin/task-statistics`

```typescript
interface TaskStatisticsResponse {
  pending_new_tasks: number;        // 待处理新任务数量（retry_count=0）
  pending_retry_tasks: number;      // 待处理重试任务数量（retry_count>0）
  processing_tasks: number;         // 正在处理任务数量
  failed_tasks: number;             // 失败任务数量
}
```

### 5. 任务状态信息响应 - TaskStatusInfo

**接口**: `GET /api/v1/admin/task-status-info`

```typescript
interface TaskStatusInfo {
  status_code: number;  // 状态码
  status_name: string;  // 状态名称
  description: string;  // 状态描述
}

// 返回数组: TaskStatusInfo[]
```

## 📊 状态码说明

### 任务状态码

| 状态码 | 状态名称 | 描述 |
|--------|----------|------|
| 0 | PENDING | 待处理 |
| 1 | PROCESSING | 处理中 |
| 2 | SUCCESS | 成功 |
| 3 | FAILED | 失败 |

### HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 🔍 使用示例

### JavaScript/TypeScript

```typescript
// 发送短信
const sendSmsResponse: ApiResponse<SmsResponse> = await fetch('/api/v1/sms/send', {
  method: 'POST',
  headers: {
    'Authorization': 'Basic ' + btoa('admin:password'),
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    phone_number: '13800138000',
    content: 'code=123456&name=张三',
    use_template: true
  })
}).then(res => res.json());

console.log(sendSmsResponse.data.task_id);

// 获取待处理任务
const pendingTasksResponse: ApiResponse<PendingTasksResponse> = await fetch(
  '/api/v1/sms/tasks/pending?app_id=my_app&limit=10',
  {
    headers: {
      'Authorization': 'Basic ' + btoa('admin:password')
    }
  }
).then(res => res.json());

console.log(`获取到 ${pendingTasksResponse.data.total_count} 个任务`);
pendingTasksResponse.data.tasks.forEach(task => {
  console.log(`任务: ${task.task_id}, 手机号: ${task.phone_number}`);
});

// 汇报发送结果
const reportResponse: ApiResponse<null> = await fetch('/api/v1/sms/report', {
  method: 'POST',
  headers: {
    'Authorization': 'Basic ' + btoa('admin:password'),
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    task_id: 'task_20231201_001',
    app_id: 'my_app',
    status: 2,
    error_message: '',
    should_retry: false
  })
}).then(res => res.json());
```

### Python

```python
import requests
import base64

# 认证头
auth_header = {
    'Authorization': f'Basic {base64.b64encode("admin:password".encode()).decode()}'
}

# 发送短信
response = requests.post('http://localhost:8000/api/v1/sms/send', 
    headers={**auth_header, 'Content-Type': 'application/json'},
    json={
        'phone_number': '13800138000',
        'content': 'code=123456&name=张三',
        'use_template': True
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"任务ID: {data['data']['task_id']}")
    print(f"最终内容: {data['data']['final_content']}")

# 汇报发送结果
report_response = requests.post('http://localhost:8000/api/v1/sms/report',
    headers={**auth_header, 'Content-Type': 'application/json'},
    json={
        'task_id': 'task_20231201_001',
        'app_id': 'my_app',
        'status': 2,
        'error_message': '',
        'should_retry': False
    }
)
```

## 📚 代码生成

这些模型定义可以用于各种代码生成工具：

- **OpenAPI Generator**: 从Swagger文档生成客户端代码
- **TypeScript**: 直接使用上述接口定义
- **Java/C#**: 使用相应的代码生成工具
- **Python**: 使用Pydantic模型或dataclass

访问 `http://localhost:8000/docs` 获取完整的OpenAPI规范文档。
