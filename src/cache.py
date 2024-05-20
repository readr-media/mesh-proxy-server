import json
from src.gql import gql_query
import src.config as config

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
        
async def check_cache_gql(backend, cache_key: str, gql_endpoint: str, gql_string: str, gql_variables: str = None, ttl: int = config.DEFAULT_GQL_TTL):
    cached_ttl, cached = await get_cache(backend, cache_key)
    if cached:
        print(f"{cache_key} hits with ttl {cached_ttl}")
        return dict(json.loads(cached))
    print(f"{cache_key} missed")
    response = gql_query(gql_endpoint, gql_string=gql_string, gql_variables=gql_variables)
    await set_cache(backend, cache_key, json.dumps(response), ttl)
    return response