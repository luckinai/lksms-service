#!/usr/bin/env python3
"""
重试间隔机制测试脚本
验证重试任务是否正确遵循RETRY_DELAY_MINUTES配置
"""

import requests
import json
import time
import base64
from datetime import datetime


class RetryDelayTester:
    """重试间隔测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8000", username: str = "admin", password: str = "admin123"):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.auth_header = self._create_auth_header()
        self.session = requests.Session()
        self.session.headers.update({"Authorization": self.auth_header})
    
    def _create_auth_header(self) -> str:
        """创建Basic Auth头"""
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        print(f"\n🔄 {method.upper()} {url}")
        
        if 'json' in kwargs:
            print(f"📤 Request: {json.dumps(kwargs['json'], indent=2, ensure_ascii=False)}")
        
        response = self.session.request(method, url, **kwargs)
        
        print(f"📥 Response [{response.status_code}]: {response.text}")
        return response
    
    def create_test_task(self) -> str:
        """创建测试任务"""
        print("\n" + "="*60)
        print("📝 创建测试任务")
        print("="*60)
        
        data = {
            "phone_number": "13900000001",
            "content": "重试间隔测试任务",
            "use_template": False,
            "source": "retry_delay_test"
        }
        
        response = self._make_request("POST", "/api/v1/sms/send", json=data)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result["data"]["task_id"]
            print(f"✅ 任务创建成功: {task_id}")
            return task_id
        else:
            print(f"❌ 任务创建失败")
            return None
    
    def get_pending_tasks(self, app_id: str = "test_app") -> list:
        """获取待处理任务"""
        params = {"app_id": app_id, "limit": 10}
        response = self._make_request("GET", "/api/v1/sms/tasks/pending", params=params)
        
        if response.status_code == 200:
            result = response.json()
            return result["data"]["tasks"]
        return []
    
    def report_failure_with_retry(self, task_id: str, app_id: str = "test_app") -> bool:
        """汇报失败并要求重试"""
        data = {
            "task_id": task_id,
            "app_id": app_id,
            "status": 3,  # FAILED
            "error_message": "模拟网络错误",
            "should_retry": True
        }
        
        response = self._make_request("POST", "/api/v1/sms/report", json=data)
        return response.status_code == 200
    
    def test_retry_delay_mechanism(self):
        """测试重试间隔机制"""
        print("\n" + "="*60)
        print("🕐 测试重试间隔机制")
        print("="*60)
        
        # 1. 创建测试任务
        task_id = self.create_test_task()
        if not task_id:
            print("❌ 无法创建测试任务，测试终止")
            return False
        
        # 2. 获取任务（应该能获取到）
        print(f"\n📋 第一次获取任务...")
        tasks = self.get_pending_tasks()
        found_task = None
        for task in tasks:
            if task["task_id"] == task_id:
                found_task = task
                break
        
        if not found_task:
            print(f"❌ 未能获取到任务 {task_id}")
            return False
        
        print(f"✅ 成功获取到任务: {task_id}")
        
        # 3. 汇报失败并要求重试
        print(f"\n📊 汇报失败并要求重试...")
        if not self.report_failure_with_retry(task_id):
            print(f"❌ 汇报失败")
            return False
        
        print(f"✅ 汇报成功，任务应该被标记为重试")
        
        # 4. 立即尝试获取任务（应该获取不到，因为还在重试间隔内）
        print(f"\n📋 立即尝试获取任务（应该获取不到）...")
        tasks = self.get_pending_tasks()
        found_task = None
        for task in tasks:
            if task["task_id"] == task_id:
                found_task = task
                break
        
        if found_task:
            print(f"❌ 意外获取到了重试任务，重试间隔机制可能有问题")
            return False
        else:
            print(f"✅ 正确：在重试间隔内无法获取到重试任务")
        
        # 5. 等待一段时间后再次尝试（这里我们等待较短时间，实际应该等待RETRY_DELAY_MINUTES）
        print(f"\n⏳ 等待重试间隔时间...")
        print(f"💡 注意：实际环境中需要等待 RETRY_DELAY_MINUTES（默认5分钟）")
        print(f"💡 为了测试方便，这里只等待10秒，您可以手动调整配置进行完整测试")
        
        time.sleep(10)
        
        # 6. 再次尝试获取任务
        print(f"\n📋 等待后再次尝试获取任务...")
        tasks = self.get_pending_tasks()
        found_task = None
        for task in tasks:
            if task["task_id"] == task_id:
                found_task = task
                break
        
        if found_task:
            print(f"✅ 在重试间隔后成功获取到重试任务")
            return True
        else:
            print(f"⚠️  仍未获取到重试任务，可能需要等待更长时间")
            print(f"💡 请检查 RETRY_DELAY_MINUTES 配置，确保等待时间足够")
            return False
    
    def get_task_statistics(self):
        """获取任务统计信息"""
        print("\n" + "="*60)
        print("📊 获取任务统计信息")
        print("="*60)
        
        response = self._make_request("GET", "/api/v1/admin/task-statistics")
        
        if response.status_code == 200:
            result = response.json()
            stats = result["data"]
            print(f"📈 统计信息:")
            print(f"   新任务: {stats['pending_new_tasks']}")
            print(f"   重试任务: {stats['pending_retry_tasks']}")
            print(f"   处理中: {stats['processing_tasks']}")
            print(f"   失败任务: {stats['failed_tasks']}")
            return True
        else:
            print(f"❌ 获取统计信息失败")
            return False
    
    def run_test(self):
        """运行完整测试"""
        print("🚀 开始重试间隔机制测试")
        print("="*60)
        
        # 获取初始统计信息
        self.get_task_statistics()
        
        # 测试重试间隔机制
        success = self.test_retry_delay_mechanism()
        
        # 获取最终统计信息
        self.get_task_statistics()
        
        print("\n" + "="*60)
        print("📋 测试结果")
        print("="*60)
        
        if success:
            print("✅ 重试间隔机制测试通过")
        else:
            print("⚠️  重试间隔机制测试需要进一步验证")
        
        print("\n💡 完整测试建议:")
        print("1. 将 RETRY_DELAY_MINUTES 设置为较小值（如1分钟）进行测试")
        print("2. 创建任务 → 获取任务 → 汇报失败重试 → 等待间隔时间 → 再次获取")
        print("3. 验证在间隔时间内无法获取重试任务")
        print("4. 验证间隔时间后可以获取重试任务")


if __name__ == "__main__":
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    username = sys.argv[2] if len(sys.argv) > 2 else "admin"
    password = sys.argv[3] if len(sys.argv) > 3 else "admin123"
    
    print(f"🔧 测试配置:")
    print(f"   服务地址: {base_url}")
    print(f"   用户名: {username}")
    print(f"   密码: {'*' * len(password)}")
    
    tester = RetryDelayTester(base_url, username, password)
    tester.run_test()
