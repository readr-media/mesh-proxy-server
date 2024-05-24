from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from src.gql import gql_stories, gql_query_forward
from src.request_body import LatestStories, GqlQuery, JsonQuery
from src.cache import check_cache_gql, check_cache_http
import os
import src.config as config
from google.cloud import pubsub_v1

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

@app.post('/pubsub')
async def pubsub(payload: dict):
  '''
  Forward pubsub request to topic. Pubsub is used to handle interactive user actions.
  '''
  topic_path = os.environ['PUBSUB_TOPIC']
  publisher = pubsub_v1.PublisherClient()
  
  ### publish data
  json_payload = payload.get('json_payload')
  future = publisher.publish(topic_path, json_payload)
  response = 'Abnormal event happened when publishing message.'
  try:
    message_id = future.result()
    response = f"Message published with ID: {message_id}."
  except Exception as e:
    response = f"Failed to publish message. Error: {e}."
  return dict({"message": response})

@app.post('/gql')
async def gql(request: GqlQuery):
  '''
  Forward gql request by http method without cache.
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  gql_payload = request.model_dump()
  response, error_message = gql_query_forward(gql_endpoint, gql_payload)
  if error_message:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"message": f"{error_message}"}
    )
  return dict(response)
  
@app.post('/gql/cache')
async def forward(request: GqlQuery):
  '''
  Forward gql request by http method with cache.
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  gql_payload = request.model_dump()
  
  response, error_message = await check_cache_http(gql_endpoint, gql_payload)
  if error_message:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"message": f"{error_message}"}
    )
  return dict(response)

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
    gql_payload = {
      "query": gql_stories_string
    }
    response, error_message = await check_cache_gql(
      gql_endpoint = gql_endpoint,
      gql_payload = gql_payload,
      ttl = config.DEFAULT_LATEST_STORIES_TTL
    )
    if error_message:
      print(f"{error_message} when fetching latest stories.")
    else:
      stories = response.get('stories', [])
      all_stories.extend(stories)
  return dict({"latest_stories:": all_stories, "num_stories": len(all_stories)})

@app.on_event("startup")
async def startup():
  NAMESPACE = os.environ.get('NAMESPACE', 'dev')
  redis_endpoint = os.environ.get('REDIS_ENDPOINT', 'redis-cache:6379')
  redis = aioredis.from_url(f"redis://{redis_endpoint}", encoding="utf8", decode_responses=True)
  FastAPICache.init(RedisBackend(redis), prefix=f"{NAMESPACE}")