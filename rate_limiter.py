import os
import json
from datetime import datetime, timedelta
from typing import Dict, Tuple

class RateLimiter:
    def __init__(self, limit: int = 3, window: int = 24):
        """
        初始化速率限制器
        :param limit: 每个时间窗口允许的请求次数
        :param window: 时间窗口小时数
        """
        self.limit = limit
        self.window = window
        self.storage_path = os.path.join(os.path.dirname(__file__), 'usage_data.json')
        # 添加白名单用户
        self.whitelist = {
            # 这里添加你的用户标识
            "b14a7b8059d9c055954c92674ce60032",  # 示例ID，需要替换为你的实际ID
        }
        self.load_data()
    
    def load_data(self):
        """加载使用数据"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                self.usage_data = json.load(f)
        else:
            self.usage_data = {}
    
    def save_data(self):
        """保存使用数据"""
        with open(self.storage_path, 'w') as f:
            json.dump(self.usage_data, f)
    
    def clean_old_data(self):
        """清理过期数据"""
        now = datetime.now()
        self.usage_data = {
            ip: data for ip, data in self.usage_data.items()
            if now - datetime.fromisoformat(data['last_reset']) < timedelta(hours=self.window)
        }
    
    def check_rate_limit(self, user_id: str) -> Tuple[bool, Dict]:
        """检查是否超出速率限制"""
        # 白名单用户无限制
        if user_id in self.whitelist:
            info = {
                'remaining_requests': '无限制',
                'reset_in': '永久有效'
            }
            return True, info
            
        # 原有的限制逻辑...
        return super().check_rate_limit(user_id)
    
    def get_usage_info(self, user_id: str) -> Tuple[bool, Dict]:
        """获取使用情况信息"""
        # 白名单用户显示无限制
        if user_id in self.whitelist:
            info = {
                'remaining_requests': '无限制',
                'reset_in': '永久有效'
            }
            return True, info
            
        # 原有的获取信息逻辑...
        return super().get_usage_info(user_id) 