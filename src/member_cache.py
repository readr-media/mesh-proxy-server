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

class MemberCache:
    """成員資訊快取系統"""
    
    def __init__(self, cache_ttl: int = 3600):  # 1小時快取
        self.cache_ttl = cache_ttl
    
    def _generate_cache_key(self, member_ids: List[str]) -> str:
        """生成快取鍵"""
        # 排序確保相同成員列表產生相同的快取鍵
        sorted_ids = sorted(member_ids)
        cache_data = ",".join(sorted_ids)
        return hashlib.sha256(cache_data.encode()).hexdigest()
    
    async def get_cached_members(self, member_ids: List[str]) -> Optional[Dict[str, Dict]]:
        """從快取取得成員資訊"""
        if not member_ids:
            return {}
        
        try:
            prefix = FastAPICache.get_prefix()
            cache_key = key_builder(f"{prefix}:members", self._generate_cache_key(member_ids))
            _, cached_data = await get_cache(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Member cache get error: {e}")
        
        return None
    
    async def set_cached_members(self, member_ids: List[str], members_data: Dict[str, Dict]):
        """設定成員資訊快取"""
        if not member_ids:
            return
        
        try:
            prefix = FastAPICache.get_prefix()
            cache_key = key_builder(f"{prefix}:members", self._generate_cache_key(member_ids))
            await set_cache(cache_key, json.dumps(members_data), self.cache_ttl)
        except Exception as e:
            print(f"Member cache set error: {e}")
    
    async def fetch_members_from_gql(self, member_ids: List[str]) -> Dict[str, Dict]:
        """從 GQL 取得成員資訊"""
        if not member_ids:
            return {}
        
        try:
            gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
            http_client = await get_http_client()
            
            query = '''
            query Members($where: MemberWhereInput!){
              members(where: $where){
                id
                customId
                name
                avatar
              }
            }
            '''
            
            variables = {
                "where": {
                    "id": {
                        "in": member_ids
                    }
                }
            }
            
            result = await http_client.post_json(gql_endpoint, {"query": query, "variables": variables}, {})
            
            if result and 'data' in result and 'members' in result['data']:
                members = result['data']['members']
                member_table = {}
                for member in members:
                    member_table[member['id']] = member
                return member_table
            
        except Exception as e:
            print(f"Fetch members from GQL error: {e}")
        
        return {}
    
    async def get_members_info(self, member_ids: List[str]) -> Dict[str, Dict]:
        """取得成員資訊（優先從快取）"""
        if not member_ids:
            return {}
        
        # 嘗試從快取取得
        cached_members = await self.get_cached_members(member_ids)
        if cached_members is not None:
            return cached_members
        
        # 從 GQL 取得
        members_data = await self.fetch_members_from_gql(member_ids)
        
        # 快取結果
        if members_data:
            await self.set_cached_members(member_ids, members_data)
        
        return members_data

# 全域成員快取實例
_member_cache = MemberCache()

def get_member_cache() -> MemberCache:
    """取得全域成員快取實例"""
    return _member_cache 