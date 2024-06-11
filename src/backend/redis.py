"""
In this file, we'll want to extend mget method to RedisBackend
"""
from fastapi_cache.backends.redis import RedisBackend

class RedisBackendExtend(RedisBackend):
    async def mget(self, keys: list[str]):
        return await self.redis.mget(keys)