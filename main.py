from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis

from src.gql import gql_query, Query
# from src.config import startup
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

### API Design
@app.get('/')
async def health_checking():
  '''
  Health checking API.
  '''
  return {"message": "Health check for mesh-proxy-server"}

@app.get('/gql')
@cache(expire=60)
async def gql_get(query: str):
  '''
  Forward gql query to GQL server by get method.
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  response = json.dumps(gql_query(gql_endpoint, gql_string=query))
  return response

@app.get("/index")
@cache(expire=180)
async def index():
    return dict(hello="world")

@app.post('/gql')
@cache(expire=3600)
async def gql_post(query: Query):
  '''
  Forward gql query to GQL server by post method.
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  query, variable = query.query, query.variable
  response = json.dumps(gql_query(gql_endpoint, gql_string=query, gql_variable=variable))
  return response

    
@app.on_event("startup")
async def startup():
  redis_endpoint = os.environ.get('REDIS_ENDPOINT', 'redis-cache:6379')
  redis = aioredis.from_url(f"redis://{redis_endpoint}", encoding="utf8", decode_responses=True)
  FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")