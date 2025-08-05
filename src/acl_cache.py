import hashlib
import time
from typing import Dict, Optional, Tuple
from functools import lru_cache
import jwt
import os
from datetime import datetime
import pytz

class ACLCache:
    """ACL 快取，避免重複的 JWT 解碼和 ACL 檢查"""
    
    def __init__(self, cache_ttl: int = 300):  # 5分鐘快取
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Tuple[Dict, float]] = {}
    
    def _generate_cache_key(self, token: str) -> str:
        """生成快取鍵"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def get(self, token: str) -> Optional[Dict]:
        """從快取取得 ACL 結果"""
        cache_key = self._generate_cache_key(token)
        if cache_key in self._cache:
            acl_header, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return acl_header
            else:
                # 過期，移除
                del self._cache[cache_key]
        return None
    
    def set(self, token: str, acl_header: Dict):
        """設定快取"""
        cache_key = self._generate_cache_key(token)
        self._cache[cache_key] = (acl_header, time.time())
        
        # 清理過期的快取項目
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def clear(self):
        """清空快取"""
        self._cache.clear()

# 全域 ACL 快取實例
_acl_cache = ACLCache()

def get_acl_cache() -> ACLCache:
    """取得全域 ACL 快取實例"""
    return _acl_cache

@lru_cache(maxsize=1000)
def cached_jwt_decode(token: str, secret: str) -> Dict:
    """快取的 JWT 解碼"""
    return jwt.decode(token, secret, algorithms=['HS256'])

def process_acl_from_payload(payload: Dict) -> Dict:
    """從 JWT payload 處理 ACL"""
    unix_current = int(datetime.now(pytz.timezone('Asia/Taipei')).timestamp())
    acl_header = {}
    
    scope = payload['scope']
    
    if scope == 'all':
        acl_header = {
            "x-access-token-scope": "mesh:member-stories:all"
        }
    else:
        # filter out expired media
        mediaArr = payload.get('media', [])
        mediaArr_filtered = set()
        for media in mediaArr:
            media_id, media_expireDate = media
            if media_expireDate < unix_current:
                continue
            mediaArr_filtered.add(media_id)
        mediaArr_str = ','.join(list(mediaArr_filtered))
        
        # filter out expired story
        storyArr = payload.get('story', [])
        storyArr_filtered = set()
        for story in storyArr:
            story_id, story_expireDate = story
            if story_expireDate < unix_current:
                continue
            storyArr_filtered.add(story_id)
        storyArr_str = ','.join(list(storyArr_filtered))
        
        # wrap acl header
        acl_header = {
            "x-access-token-scope": "mesh:member-stories:media",
            "x-access-token-media": mediaArr_str,
            "x-access-token-story": storyArr_str,
        }
    
    return acl_header 