from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.requests import Request
from redis import asyncio as aioredis

from src.gql import gql_query, Query
from src.key_builder import gql_key_builder
import os
import json

### App related variables
app = FastAPI()
origins = ["*"]
methods = ["*"]
headers = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = methods,
    allow_headers = headers
)
NAMESPACE = 'dev'

### API Design
@app.get('/')
async def health_checking():
  '''
  Health checking API.
  '''
  return dict(message="Health check for mesh-proxy-server")

@app.post('/gql')
async def gql_post(query: Query):
  '''
  Forward gql query to GQL server by post method. 
  Because post method is not cacheable in fastapi-cache, we should cache it manually.
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  query, variable, ttl = query.query, query.variable, query.ttl
  
  ### check cache in redis
  prefix = FastAPICache.get_prefix()
  redis  = FastAPICache.get_backend()
  cache_key = gql_key_builder(prefix, query.model_dump_json())
  cached_result = await redis.get(cache_key)
  if cached_result:
      return dict(json.loads(cached_result))
  ### cache misses
  response = gql_query(gql_endpoint, gql_string=query, gql_variable=variable)
  await redis.set(cache_key, json.dumps(response), expire=ttl)
  return dict(response)

@app.on_event("startup")
async def startup():
  redis_endpoint = os.environ.get('REDIS_ENDPOINT', 'redis-cache:6379')
  redis = aioredis.from_url(f"redis://{redis_endpoint}", encoding="utf8", decode_responses=True)
  FastAPICache.init(RedisBackend(redis), prefix=f"cache-{NAMESPACE}")