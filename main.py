from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from starlette.responses import Response
from redis import asyncio as aioredis
import redis


from src.gql import gql_query, Query
from src.key_builder import gql_key_builder
from src.cache import get_cache, set_cache
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

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = int(os.environ.get("REDIS_PORT", 6379))
redis_client = redis.StrictRedis(host=redis_host, port=redis_port)

### API Design
@app.get('/')
async def health_checking():
  '''
  Health checking API. You can only use @cache decorator to get method.
  '''
  return dict(message="Health check for mesh-proxy-server")

@app.get('/test')
async def test():
  value = redis_client.incr("counter", 1)
  return f"Visitor number: {value}"

@app.post('/gql')
async def gql_post(query: Query):
  '''
  Forward gql query to GQL server by post method. 
  Because post method is not cacheable in fastapi-cache, we should cache it manually.
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  gql_string, gql_variable, ttl = query.query, query.variable, query.ttl
  
  ### check cache in redis
  prefix = FastAPICache.get_prefix()
  backend  = FastAPICache.get_backend()
  cache_key = gql_key_builder(prefix, query.model_dump_json())
  
  # cache checking
  cached_ttl, cached = await get_cache(backend, cache_key)
  if cached:
    print(f"{cache_key} hits with ttl {cached_ttl}")
    return dict(json.loads(cached))
  print(f"{cache_key} missed")
  response = gql_query(gql_endpoint, gql_string=gql_string, gql_variable=gql_variable)
  await set_cache(backend, cache_key, json.dumps(response), ttl)
  return dict(response)

# @app.on_event("startup")
# async def startup():
#   NAMESPACE = os.environ.get('NAMESPACE', 'dev')
#   redis_endpoint = os.environ.get('REDIS_ENDPOINT', 'redis-cache:6379')
#   redis = aioredis.from_url(f"redis://{redis_endpoint}", encoding="utf8", decode_responses=True)
#   FastAPICache.init(RedisBackend(redis), prefix=f"cache-{NAMESPACE}")