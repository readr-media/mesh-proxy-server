import hashlib
import json
import time
from typing import Dict, List, Optional, Any
from fastapi_cache import FastAPICache
from src.tool import key_builder
from src.cache import get_cache, set_cache
from src.http_client import get_http_client
import src.config as config
import os

class PublisherCache:
    """發布者快取系統"""
    
    def __init__(self, cache_ttl: int = 3600):  # 1小時快取
        self.cache_ttl = cache_ttl
    
    def _generate_cache_key(self, publisher_ids: List[str]) -> str:
        """生成快取鍵"""
        # 排序確保相同發布者列表產生相同的快取鍵
        sorted_ids = sorted(publisher_ids)
        cache_data = ",".join(sorted_ids)
        return hashlib.sha256(cache_data.encode()).hexdigest()
    
    async def get_cached_publishers(self, publisher_ids: List[str]) -> Optional[Dict[str, Dict]]:
        """從快取取得發布者資訊"""
        if not publisher_ids:
            return {}
        
        try:
            prefix = FastAPICache.get_prefix()
            cache_key = key_builder(f"{prefix}:publishers", self._generate_cache_key(publisher_ids))
            _, cached_data = await get_cache(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Publisher cache get error: {e}")
        
        return None
    
    async def set_cached_publishers(self, publisher_ids: List[str], publishers_data: Dict[str, Dict]):
        """設定發布者資訊快取"""
        if not publisher_ids:
            return
        
        try:
            prefix = FastAPICache.get_prefix()
            cache_key = key_builder(f"{prefix}:publishers", self._generate_cache_key(publisher_ids))
            await set_cache(cache_key, json.dumps(publishers_data), self.cache_ttl)
        except Exception as e:
            print(f"Publisher cache set error: {e}")
    
    async def fetch_publishers_from_gql(self, publisher_ids: List[str]) -> Dict[str, Dict]:
        """從 GQL 取得發布者資訊"""
        if not publisher_ids:
            return {}
        
        try:
            gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
            http_client = await get_http_client()
            
            query = '''
            query Publishers($where: PublisherWhereInput!){
              publishers(where: $where){
                id
                title
                customId
                admin{
                  firebaseId
                }
              }
            }
            '''
            
            variables = {
                "where": {
                    "id": {
                        "in": publisher_ids
                    }
                }
            }
            
            result = await http_client.post_json(gql_endpoint, {"query": query, "variables": variables}, {})
            
            if result and 'data' in result and 'publishers' in result['data']:
                publishers = result['data']['publishers']
                publisher_table = {}
                for publisher in publishers:
                    publisher_table[publisher['id']] = publisher
                return publisher_table
            
        except Exception as e:
            print(f"Fetch publishers from GQL error: {e}")
        
        return {}
    
    async def get_publishers_info(self, publisher_ids: List[str]) -> Dict[str, Dict]:
        """取得發布者資訊（優先從快取）"""
        if not publisher_ids:
            return {}
        
        # 嘗試從快取取得
        cached_publishers = await self.get_cached_publishers(publisher_ids)
        if cached_publishers is not None:
            return cached_publishers
        
        # 從 GQL 取得
        publishers_data = await self.fetch_publishers_from_gql(publisher_ids)
        
        # 快取結果
        if publishers_data:
            await self.set_cached_publishers(publisher_ids, publishers_data)
        
        return publishers_data
    
    async def get_publisher_admin_info(self, publisher_id: str) -> Optional[Dict]:
        """取得單個發布者的管理員資訊"""
        try:
            gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
            http_client = await get_http_client()
            
            query = '''
            query Publisher($where: PublisherWhereInput!){
              publisher(where: $where){
                customId
                admin{
                  firebaseId
                }
              }
            }
            '''
            
            variables = {
                "where": {
                    "id": {
                        "equals": publisher_id
                    }
                }
            }
            
            result = await http_client.post_json(gql_endpoint, {"query": query, "variables": variables}, {})
            
            if result and 'data' in result and 'publisher' in result['data']:
                return result['data']['publisher']
            
        except Exception as e:
            print(f"Fetch publisher admin from GQL error: {e}")
        
        return None

# 全域發布者快取實例
_publisher_cache = PublisherCache()

def get_publisher_cache() -> PublisherCache:
    """取得全域發布者快取實例"""
    return _publisher_cache 