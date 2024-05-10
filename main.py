from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

from redis import asyncio as aioredis
from src.gql import gql_fetch
import os

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
  Health checking API.
  '''
  return {"message": "Health check for mesh-proxy-server"}

@app.get('/gql')
@cache(expire=60)
async def gql(query: str):
  '''
  Forward gql query to GQL server.
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  response = gql_fetch(gql_endpoint, gql_string=query)
  return {"message": response}

@app.on_event("startup")
async def startup():
  redis_endpoint = os.environ.get('REDIS_ENDPOINT', 'redis_cache:6379')
  redis = aioredis.from_url(f"redis://{redis_endpoint}")
  FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")