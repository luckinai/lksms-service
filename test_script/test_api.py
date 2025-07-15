#!/usr/bin/env python3
"""
LKSMS Service API测试脚本
测试所有主要API接口功能
"""

import requests
import json
import time
from typing import Dict, Any
import base64


class LKSMSAPITester:
    """LKSMS API测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8000", username: str = "admin", password: str = "your_secure_password"):
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
    
    def test_health_check(self) -> bool:
        """测试健康检查"""
        print("\n" + "="*50)
        print("🏥 测试健康检查")
        print("="*50)
        
        try:
            response = self._make_request("GET", "/health")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return False
    
    def test_create_template(self) -> bool:
        """测试创建模板"""
        print("\n" + "="*50)
        print("📝 测试创建模板")
        print("="*50)
        
        try:
            data = {
                "template_name": "测试模板",
                "template_content": "您的验证码是{code}，用户{name}，请在{time}分钟内使用。"
            }
            response = self._make_request("POST", "/api/v1/admin/template", json=data)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 创建模板失败: {e}")
            return False
    
    def test_create_default_sms(self) -> bool:
        """测试创建默认短信内容"""
        print("\n" + "="*50)
        print("📱 测试创建默认短信内容")
        print("="*50)
        
        try:
            # 创建使用模板的默认内容
            data1 = {
                "phone_number": "13900139001",
                "content": "code=888888&name=测试用户&time=5",
                "use_template": True
            }
            response1 = self._make_request("POST", "/api/v1/admin/default-sms", json=data1)
            
            # 创建不使用模板的默认内容
            data2 = {
                "phone_number": "13900139002",
                "content": "欢迎使用LKSMS服务！",
                "use_template": False
            }
            response2 = self._make_request("POST", "/api/v1/admin/default-sms", json=data2)
            
            return response1.status_code == 200 and response2.status_code == 200
        except Exception as e:
            print(f"❌ 创建默认短信内容失败: {e}")
            return False
    
    def test_send_sms_with_content(self) -> str:
        """测试发送短信（带内容）"""
        print("\n" + "="*50)
        print("📤 测试发送短信（带内容）")
        print("="*50)
        
        try:
            data = {
                "phone_number": "13800138000",
                "content": "您的验证码是123456，请及时使用。",
                "use_template": False,
                "source": "test_system"
            }
            response = self._make_request("POST", "/api/v1/sms/send", json=data)
            
            if response.status_code == 200:
                result = response.json()
                return result["data"]["task_id"]
            return None
        except Exception as e:
            print(f"❌ 发送短信失败: {e}")
            return None
    
    def test_send_sms_with_template(self) -> str:
        """测试发送短信（使用模板）"""
        print("\n" + "="*50)
        print("📤 测试发送短信（使用模板）")
        print("="*50)
        
        try:
            data = {
                "phone_number": "13800138001",
                "content": "code=654321&name=张三&time=10",
                "use_template": True,
                "source": "test_system"
            }
            response = self._make_request("POST", "/api/v1/sms/send", json=data)
            
            if response.status_code == 200:
                result = response.json()
                return result["data"]["task_id"]
            return None
        except Exception as e:
            print(f"❌ 发送短信（模板）失败: {e}")
            return None
    
    def test_send_sms_default_content(self) -> str:
        """测试发送短信（默认内容）"""
        print("\n" + "="*50)
        print("📤 测试发送短信（默认内容）")
        print("="*50)
        
        try:
            data = {
                "phone_number": "13900139001",  # 使用之前创建的默认内容
                "source": "test_system"
            }
            response = self._make_request("POST", "/api/v1/sms/send", json=data)
            
            if response.status_code == 200:
                result = response.json()
                return result["data"]["task_id"]
            return None
        except Exception as e:
            print(f"❌ 发送短信（默认内容）失败: {e}")
            return None
    
    def test_query_task(self, task_id: str) -> bool:
        """测试查询任务状态"""
        print("\n" + "="*50)
        print(f"🔍 测试查询任务状态: {task_id}")
        print("="*50)
        
        try:
            response = self._make_request("GET", f"/api/v1/sms/task/{task_id}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 查询任务失败: {e}")
            return False
    
    def test_get_pending_tasks(self) -> list:
        """测试获取待处理任务"""
        print("\n" + "="*50)
        print("📋 测试获取待处理任务")
        print("="*50)
        
        try:
            params = {"app_id": "test_app_001", "limit": 5}
            response = self._make_request("GET", "/api/v1/sms/tasks/pending", params=params)
            
            if response.status_code == 200:
                result = response.json()
                # 新的响应格式包含tasks数组
                return result["data"]["tasks"] if "tasks" in result["data"] else result["data"]
            return []
        except Exception as e:
            print(f"❌ 获取待处理任务失败: {e}")
            return []
    
    def test_report_result(self, task_id: str, success: bool = True) -> bool:
        """测试汇报发送结果"""
        print("\n" + "="*50)
        print(f"📊 测试汇报发送结果: {task_id}")
        print("="*50)

        try:
            data = {
                "task_id": task_id,
                "app_id": "test_app_001",
                "status": 2 if success else 3,
                "error_message": "" if success else "发送失败测试",
                "should_retry": False if success else True  # 失败时测试重试
            }
            response = self._make_request("POST", "/api/v1/sms/report", json=data)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 汇报结果失败: {e}")
            return False

    def test_admin_interfaces(self) -> bool:
        """测试管理接口"""
        print("\n" + "="*50)
        print("🔧 测试管理接口")
        print("="*50)

        try:
            # 测试获取任务统计
            response1 = self._make_request("GET", "/api/v1/admin/task-statistics")

            # 测试获取任务状态信息
            response2 = self._make_request("GET", "/api/v1/admin/task-status-info")

            # 测试手动恢复僵尸任务
            response3 = self._make_request("POST", "/api/v1/admin/recover-zombie-tasks")

            return all(r.status_code == 200 for r in [response1, response2, response3])
        except Exception as e:
            print(f"❌ 管理接口测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始LKSMS API测试")
        print("="*60)
        
        results = []
        
        # 1. 健康检查
        results.append(("健康检查", self.test_health_check()))
        
        # 2. 创建模板
        results.append(("创建模板", self.test_create_template()))
        
        # 3. 创建默认短信内容
        results.append(("创建默认短信内容", self.test_create_default_sms()))
        
        # 4. 发送短信（带内容）
        task_id1 = self.test_send_sms_with_content()
        results.append(("发送短信（带内容）", task_id1 is not None))
        
        # 5. 发送短信（使用模板）
        task_id2 = self.test_send_sms_with_template()
        results.append(("发送短信（使用模板）", task_id2 is not None))
        
        # 6. 发送短信（默认内容）
        task_id3 = self.test_send_sms_default_content()
        results.append(("发送短信（默认内容）", task_id3 is not None))
        
        # 7. 查询任务状态
        if task_id1:
            results.append(("查询任务状态", self.test_query_task(task_id1)))
        
        # 8. 获取待处理任务
        pending_tasks = self.test_get_pending_tasks()
        results.append(("获取待处理任务", len(pending_tasks) > 0))
        
        # 9. 汇报发送结果
        if pending_tasks:
            task_to_report = pending_tasks[0]["task_id"]
            results.append(("汇报发送结果（成功）", self.test_report_result(task_to_report, True)))

            if len(pending_tasks) > 1:
                task_to_report2 = pending_tasks[1]["task_id"]
                results.append(("汇报发送结果（失败）", self.test_report_result(task_to_report2, False)))

        # 10. 测试管理接口
        results.append(("管理接口测试", self.test_admin_interfaces()))
        
        # 输出测试结果
        print("\n" + "="*60)
        print("📊 测试结果汇总")
        print("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{test_name:<20} {status}")
            if success:
                passed += 1
        
        print(f"\n总计: {passed}/{total} 个测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！")
        else:
            print("⚠️  部分测试失败，请检查服务状态和配置")


if __name__ == "__main__":
    # 可以通过命令行参数自定义配置
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    username = sys.argv[2] if len(sys.argv) > 2 else "admin"
    password = sys.argv[3] if len(sys.argv) > 3 else "your_secure_password"
    
    print(f"🔧 测试配置:")
    print(f"   服务地址: {base_url}")
    print(f"   用户名: {username}")
    print(f"   密码: {'*' * len(password)}")
    
    tester = LKSMSAPITester(base_url, username, password)
    tester.run_all_tests()
