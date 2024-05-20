from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from src.gql import gql_query, Query
from src.key_builder import gql_key_builder
from src.cache import check_cache_gql
import os
import json
import src.config as config

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

### API Design
@app.get('/')
async def health_checking():
  '''
  Health checking API. You can only use @cache decorator to get method.
  '''
  return dict(message="Health check for mesh-proxy-server")

@app.post('/new_stories')
async def new_stories():
  return dict(message="new_stories")

@app.post('/gql')
async def gql_post(query: Query):
  '''
  Forward gql query to GQL server by post method. 
  Because post method is not cacheable in fastapi-cache, we should cache it manually.
  The range of ttl is [3,600], default is 60.
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  gql_string, gql_variable, ttl = query.query, query.variable, query.ttl
  
  ### validate input data
  if ttl>config.MAX_GQL_TTL or ttl<config.MIN_GQL_TTL:
    return dict(message="Invalid input ttl")
  
  ### build cache key
  prefix = FastAPICache.get_prefix()
  backend  = FastAPICache.get_backend()
  cache_key = gql_key_builder(prefix, query.model_dump_json())
  
  ### cache checking
  response = await check_cache_gql(
    backend = backend,
    cache_key = cache_key,
    gql_endpoint = gql_endpoint,
    gql_string = gql_string,
    gql_variable = gql_variable,
    ttl = ttl
  )
  return dict(response)

@app.on_event("startup")
async def startup():
  NAMESPACE = os.environ.get('NAMESPACE', 'dev')
  redis_endpoint = os.environ.get('REDIS_ENDPOINT', 'redis-cache:6379')
  redis = aioredis.from_url(f"redis://{redis_endpoint}", encoding="utf8", decode_responses=True)
  FastAPICache.init(RedisBackend(redis), prefix=f"cache-{NAMESPACE}")