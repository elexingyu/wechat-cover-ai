import os
import json
from datetime import datetime, timedelta
from typing import Tuple, Dict

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
            "admin",  # 管理员用户名
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
            user_id: data for user_id, data in self.usage_data.items()
            if now - datetime.fromisoformat(data['last_reset']) < timedelta(hours=self.window)
        }
    
    def get_usage_info(self, user_id: str) -> Tuple[bool, Dict]:
        """
        获取使用情况信息
        :param user_id: 用户标识
        :return: (是否允许请求, 使用信息)
        """
        # 白名单用户无限制
        if user_id in self.whitelist:
            return True, {
                'remaining_requests': '无限制',
                'reset_in': '永久有效'
            }
        
        # 清理过期数据
        self.clean_old_data()
        
        now = datetime.now()
        
        # 如果是新用户或者数据已过期
        if user_id not in self.usage_data:
            self.usage_data[user_id] = {
                'count': 0,
                'last_reset': now.isoformat()
            }
            self.save_data()
        
        user_data = self.usage_data[user_id]
        last_reset = datetime.fromisoformat(user_data['last_reset'])
        
        # 如果超过时间窗口，重置计数
        if now - last_reset > timedelta(hours=self.window):
            user_data['count'] = 0
            user_data['last_reset'] = now.isoformat()
            self.save_data()
        
        # 计算剩余请求次数和重置时间
        remaining = self.limit - user_data['count']
        reset_time = last_reset + timedelta(hours=self.window)
        reset_in = reset_time - now
        
        hours = int(reset_in.total_seconds() // 3600)
        minutes = int((reset_in.total_seconds() % 3600) // 60)
        
        info = {
            'remaining_requests': remaining,
            'reset_in': f'{hours}小时{minutes}分钟后重置'
        }
        
        return remaining > 0, info
    
    def check_rate_limit(self, user_id: str) -> Tuple[bool, Dict]:
        """
        检查是否超出速率限制
        :param user_id: 用户标识
        :return: (是否允许请求, 使用信息)
        """
        allowed, info = self.get_usage_info(user_id)
        
        if allowed and user_id not in self.whitelist:
            self.usage_data[user_id]['count'] += 1
            self.save_data()
        
        return allowed, info 