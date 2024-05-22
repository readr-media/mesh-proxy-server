from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from src.gql import Query, LatestStories, Forward, gql_stories, gql_query_forward
from src.key_builder import gql_key_builder
from src.cache import check_cache_gql, check_cache_http
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

@app.post('/latest_stories')
async def latest_stories(latestStories: LatestStories):
  '''
  Get latest stories by publisher ids. Default latest_stories_num for each publisher is 30.
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  publishers = latestStories.publishers
  if len(publishers)==0:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": f"Invalid publishers field, it cannot be empty list."},
    )
    
  all_stories = []
  for publisher_id in publishers:
    gql_stories_string = gql_stories.format(ID=publisher_id, TAKE=config.DEFAULT_LATEST_STORIES_NUM)
    
    ### build cache key
    prefix = FastAPICache.get_prefix()
    backend  = FastAPICache.get_backend()
    cache_key = gql_key_builder(prefix, gql_stories_string)
    
    ### cache checking
    response = await check_cache_gql(
      backend = backend,
      cache_key = cache_key,
      gql_endpoint = gql_endpoint,
      gql_string = gql_stories_string,
      gql_variables = None,
      ttl = config.DEFAULT_LATEST_STORIES_TTL
    )
    stories = response.get('stories', [])
    all_stories.extend(stories)
  return dict({"latest_stories:": all_stories, "num_stories": len(all_stories)})

@app.post('/gql')
async def gql_post(query: Query):
  '''
  Forward gql query to GQL server by post method. 
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  gql_payload = query.model_dump()
  ttl = gql_payload['ttl']
  
  ### validate input data
  if ttl>config.MAX_GQL_TTL or ttl<config.MIN_GQL_TTL:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": f"Invalid ttl value."},
    )
  
  ### cache checking
  response, error_message = await check_cache_gql(
    gql_endpoint = gql_endpoint,
    gql_payload = gql_payload,
    ttl = ttl
  )
  if error_message:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"message": f"{error_message}"}
    )
  return dict({"data": response})

@app.post('/gql_mobile')
async def gql_post_mobile(query: Query):
  '''
  Forward gql query to GQL server by post method and it's for mobile. 
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  gql_payload = query.model_dump()
  ttl = gql_payload['ttl']
  
  ### validate input data
  if ttl>config.MAX_GQL_TTL or ttl<config.MIN_GQL_TTL:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": f"Invalid ttl value."},
    )
  
  ### cache checking
  response, error_message = await check_cache_gql(
    gql_endpoint = gql_endpoint,
    gql_payload = gql_payload,
    ttl = ttl
  )
  if error_message:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"message": f"{error_message}"}
    )
  return dict(response)

@app.post('/forward')
async def forward(forward: Forward):
  '''
  Forward gql request by http method directly.
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  gql_payload = forward.model_dump()
  
  response, error_message = await check_cache_http(gql_endpoint, gql_payload)
  if error_message:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"message": f"{error_message}"}
    )
  return dict(response)

@app.on_event("startup")
async def startup():
  NAMESPACE = os.environ.get('NAMESPACE', 'dev')
  redis_endpoint = os.environ.get('REDIS_ENDPOINT', 'redis-cache:6379')
  redis = aioredis.from_url(f"redis://{redis_endpoint}", encoding="utf8", decode_responses=True)
  FastAPICache.init(RedisBackend(redis), prefix=f"{NAMESPACE}")