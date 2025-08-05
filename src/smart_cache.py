import hashlib
import json
import time
# 確保 JSON 優化生效
import src.json_optimizer
from typing import Any, Dict, Optional, List
from functools import wraps
import asyncio
from src.cache import get_cache, set_cache, mget_cache
from src.json_optimizer import fast_json_dumps, fast_json_loads

class SmartCache:
    """智能快取策略，根據請求特點自動決定快取策略"""
    
    def __init__(self):
        self.cache_patterns = {
            # 查詢類請求：快取時間較長
            'query': {
                'ttl': 300,  # 5分鐘
                'patterns': ['query', 'get', 'list', 'search']
            },
            # 讀取類請求：中等快取時間
            'read': {
                'ttl': 60,   # 1分鐘
                'patterns': ['read', 'fetch', 'retrieve']
            },
            # 動態類請求：短快取時間
            'dynamic': {
                'ttl': 10,   # 10秒
                'patterns': ['notifications', 'socialpage', 'latest']
            },
            # 實時類請求：不快取
            'realtime': {
                'ttl': 0,    # 不快取
                'patterns': ['pubsub', 'stream', 'live']
            }
        }
    
    def _generate_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """生成快取鍵"""
        # 排序參數以確保一致性
        sorted_params = sorted(params.items())
        param_str = fast_json_dumps(sorted_params)
        
        # 組合端點和參數
        key_data = f"{endpoint}:{param_str}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _determine_cache_strategy(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """決定快取策略"""
        endpoint_lower = endpoint.lower()
        
        # 檢查是否匹配任何模式
        for strategy_name, strategy in self.cache_patterns.items():
            for pattern in strategy['patterns']:
                if pattern in endpoint_lower:
                    return {
                        'ttl': strategy['ttl'],
                        'strategy': strategy_name,
                        'should_cache': strategy['ttl'] > 0
                    }
        
        # 預設策略：動態類
        return {
            'ttl': 10,
            'strategy': 'default',
            'should_cache': True
        }
    
    async def get_cached_data(self, endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
        """獲取快取的資料"""
        cache_key = self._generate_cache_key(endpoint, params)
        ttl, cached_data = await get_cache(cache_key)
        
        if cached_data:
            try:
                return fast_json_loads(cached_data)
            except:
                return None
        
        return None
    
    async def set_cached_data(self, endpoint: str, params: Dict[str, Any], data: Any):
        """設定快取資料"""
        strategy = self._determine_cache_strategy(endpoint, params)
        
        if not strategy['should_cache']:
            return
        
        cache_key = self._generate_cache_key(endpoint, params)
        data_str = fast_json_dumps(data)
        
        await set_cache(cache_key, data_str, strategy['ttl'])
    
    async def invalidate_pattern(self, pattern: str):
        """根據模式使快取失效（需要 Redis 支援）"""
        # 這裡需要 Redis 的 SCAN 功能來實現模式匹配的失效
        # 簡化實現：記錄需要失效的模式
        pass

def smart_cache_decorator(endpoint: str):
    """智能快取裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 提取參數
            params = {}
            if args:
                # 第一個參數通常是 request 物件
                if hasattr(args[0], 'model_dump'):
                    params.update(args[0].model_dump())
                elif hasattr(args[0], 'dict'):
                    params.update(args[0].dict())
            
            params.update(kwargs)
            
            # 嘗試從快取獲取
            smart_cache = SmartCache()
            cached_data = await smart_cache.get_cached_data(endpoint, params)
            
            if cached_data is not None:
                return cached_data
            
            # 執行原始函數
            result = await func(*args, **kwargs)
            
            # 快取結果
            await smart_cache.set_cached_data(endpoint, params, result)
            
            return result
        
        return wrapper
    return decorator

# 全域智能快取實例
_smart_cache = SmartCache()

def get_smart_cache() -> SmartCache:
    """取得全域智能快取實例"""
    return _smart_cache

# 便捷函數
async def smart_get_cached(endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
    """智能獲取快取資料"""
    return await _smart_cache.get_cached_data(endpoint, params)

async def smart_set_cached(endpoint: str, params: Dict[str, Any], data: Any):
    """智能設定快取資料"""
    await _smart_cache.set_cached_data(endpoint, params, data) 