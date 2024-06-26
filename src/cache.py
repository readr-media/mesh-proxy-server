from fastapi_cache import FastAPICache

async def mget_cache(cache_keys: list[str]):
    data = None
    try:
        backend  = FastAPICache.get_backend()
        data = await backend.mget(cache_keys)
    except Exception as e:
        print(f"Error retrieving data by mget from backend, error_message: {e}")
    return data

async def get_cache(backend, cache_key: str):
    try:
        ttl, cached = await backend.get_with_ttl(cache_key)
    except Exception:
        print(f"Error retrieving cache key '{cache_key}' from backend")
        ttl, cached = 0, None
    return ttl, cached

async def set_cache(backend, cache_key: str, cache_value: str, ttl: int):
    try:
        await backend.set(cache_key, cache_value, expire=ttl)
    except Exception:
        print(f"Error setting cache key '{cache_key}' from backend")