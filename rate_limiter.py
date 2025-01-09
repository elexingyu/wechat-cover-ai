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
    
    def check_rate_limit(self, ip: str) -> Tuple[bool, Dict]:
        """
        检查是否超出速率限制
        :return: (是否允许请求, 使用情况信息)
        """
        now = datetime.now()
        self.clean_old_data()
        
        if ip not in self.usage_data:
            self.usage_data[ip] = {
                'count': 0,
                'last_reset': now.isoformat()
            }
        
        data = self.usage_data[ip]
        last_reset = datetime.fromisoformat(data['last_reset'])
        
        # 检查是否需要重置计数器
        if now - last_reset >= timedelta(hours=self.window):
            data['count'] = 0
            data['last_reset'] = now.isoformat()
        
        # 检查是否超出限制
        if data['count'] >= self.limit:
            next_reset = last_reset + timedelta(hours=self.window)
            remaining_time = next_reset - now
            hours = remaining_time.seconds // 3600
            minutes = (remaining_time.seconds % 3600) // 60
            
            info = {
                'remaining_requests': 0,
                'reset_in': f"{hours}小时{minutes}分钟后重置"
            }
            return False, info
        
        # 更新计数
        data['count'] += 1
        self.save_data()
        
        info = {
            'remaining_requests': self.limit - data['count'],
            'reset_in': f"{self.window}小时内"
        }
        return True, info 
    
    def get_usage_info(self, ip: str) -> Tuple[bool, Dict]:
        """
        获取使用情况信息（不增加计数）
        """
        now = datetime.now()
        self.clean_old_data()
        
        if ip not in self.usage_data:
            info = {
                'remaining_requests': self.limit,
                'reset_in': f"{self.window}小时内"
            }
            return True, info
        
        data = self.usage_data[ip]
        last_reset = datetime.fromisoformat(data['last_reset'])
        
        # 检查是否需要重置计数器
        if now - last_reset >= timedelta(hours=self.window):
            info = {
                'remaining_requests': self.limit,
                'reset_in': f"{self.window}小时内"
            }
            return True, info
        
        # 返回当前使用情况
        if data['count'] >= self.limit:
            next_reset = last_reset + timedelta(hours=self.window)
            remaining_time = next_reset - now
            hours = remaining_time.seconds // 3600
            minutes = (remaining_time.seconds % 3600) // 60
            
            info = {
                'remaining_requests': 0,
                'reset_in': f"{hours}小时{minutes}分钟后重置"
            }
            return False, info
        
        info = {
            'remaining_requests': self.limit - data['count'],
            'reset_in': f"{self.window}小时内"
        }
        return True, info 