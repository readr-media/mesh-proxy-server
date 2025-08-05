import hashlib
import json
import time
from typing import Dict, List, Optional, Any
from fastapi_cache import FastAPICache
from src.tool import key_builder
from src.cache import get_cache, set_cache
import src.config as config

class NotificationCache:
    """通知快取系統"""
    
    def __init__(self, cache_ttl: int = 300):  # 5分鐘快取
        self.cache_ttl = cache_ttl
    
    def _generate_cache_key(self, member_id: str, index: int, take: int) -> str:
        """生成快取鍵"""
        cache_data = f"{member_id}:{index}:{take}"
        return hashlib.sha256(cache_data.encode()).hexdigest()
    
    async def get_cached_notifications(self, member_id: str, index: int, take: int) -> Optional[Dict]:
        """從快取取得通知"""
        try:
            prefix = FastAPICache.get_prefix()
            cache_key = key_builder(f"{prefix}:notifications", self._generate_cache_key(member_id, index, take))
            _, cached_data = await get_cache(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Notification cache get error: {e}")
        
        return None
    
    async def set_cached_notifications(self, member_id: str, index: int, take: int, notifications: Dict):
        """設定通知快取"""
        try:
            prefix = FastAPICache.get_prefix()
            cache_key = key_builder(f"{prefix}:notifications", self._generate_cache_key(member_id, index, take))
            await set_cache(cache_key, json.dumps(notifications), self.cache_ttl)
        except Exception as e:
            print(f"Notification cache set error: {e}")
    
    async def invalidate_member_cache(self, member_id: str):
        """使特定成員的快取失效"""
        # 這裡可以實作更精細的快取失效邏輯
        # 目前先簡單處理，實際可以根據需求調整
        pass

# 全域通知快取實例
_notification_cache = NotificationCache()

def get_notification_cache() -> NotificationCache:
    """取得全域通知快取實例"""
    return _notification_cache 