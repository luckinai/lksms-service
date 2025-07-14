from enum import IntEnum


class TaskStatus(IntEnum):
    """任务状态枚举"""
    PENDING = 0      # 待处理
    PROCESSING = 1   # 处理中
    SUCCESS = 2      # 成功
    FAILED = 3       # 失败
    
    @classmethod
    def get_description(cls, status: int) -> str:
        """获取状态描述"""
        descriptions = {
            cls.PENDING: "待处理",
            cls.PROCESSING: "处理中", 
            cls.SUCCESS: "成功",
            cls.FAILED: "失败"
        }
        return descriptions.get(status, "未知状态")
