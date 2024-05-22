import json
from fastapi_cache import FastAPICache
from src.key_builder import gql_key_builder
from src.gql import gql_query, gql_query_forward
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
        
# async def check_cache_gql(backend, cache_key: str, gql_endpoint: str, gql_string: str, gql_variables: str = None, operation_name: str=None, ttl: int = config.DEFAULT_GQL_TTL):
#     cached_ttl, cached = await get_cache(backend, cache_key)
#     if cached:
#         print(f"{cache_key} hits with ttl {cached_ttl}")
#         return dict(json.loads(cached))
#     print(f"{cache_key} missed")
#     response, error_message = gql_query(gql_endpoint, gql_string=gql_string, gql_variables=gql_variables, operation_name=operation_name)
#     if response and (error_message is None):
#         await set_cache(backend, cache_key, json.dumps(response), ttl)
#     return response, error_message

async def check_cache_gql(gql_endpoint: str, gql_payload: dict, ttl: int = config.DEFAULT_GQL_TTL):
    ### build cache key
    prefix = FastAPICache.get_prefix()
    backend  = FastAPICache.get_backend()
    cache_key = gql_key_builder(f"{prefix}:gql", json.dumps(gql_payload))
    
    ### unpack payload
    gql_string = gql_payload.get('query', None)
    gql_variables = gql_payload.get('variables', None)
    operation_name = gql_payload.get('operationName', None)
    
    ### check cache
    cached_ttl, cached = await get_cache(backend, cache_key)
    if cached:
        print(f"{cache_key} hits with ttl {cached_ttl}")
        return dict(json.loads(cached)), None
    print(f"{cache_key} missed")
    response, error_message = gql_query(gql_endpoint, gql_string=gql_string, gql_variables=gql_variables, operation_name=operation_name)
    if response and (error_message is None):
        await set_cache(backend, cache_key, json.dumps(response), ttl)
    return response, error_message

async def check_cache_http(gql_endpoint: str, gql_payload: dict, ttl: int=config.DEFAULT_GQL_TTL):
    ### build cache key
    prefix = FastAPICache.get_prefix()
    backend  = FastAPICache.get_backend()
    cache_key = gql_key_builder(f"{prefix}:http", json.dumps(gql_payload))
    
    ### check cache
    cached_ttl, cached = await get_cache(backend, cache_key)
    if cached:
        print(f"{cache_key} hits with ttl {cached_ttl}")
        return dict(json.loads(cached)), None
    print(f"{cache_key} missed")
    response, error_message = gql_query_forward(gql_endpoint, gql_payload)
    if response and (error_message is None):
        await set_cache(backend, cache_key, json.dumps(response), ttl)
    return response, error_message