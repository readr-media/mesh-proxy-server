from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi_cache import FastAPICache
from src.backend.redis import RedisBackendExtend
from redis import asyncio as aioredis

from src.gql import gql_query_forward
from src.request_body import LatestStories, GqlQuery
from src.key_builder import key_builder
from src.cache import check_cache_http, mget_cache
import os
from google.cloud import pubsub_v1
import json
from datetime import datetime
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

@app.post('/pubsub')
async def pubsub(request: dict):
  '''
  Forward pubsub messages
  '''
  topic_path = os.environ['PUBSUB_TOPIC']
  publisher = pubsub_v1.PublisherClient()
  
  print("pubsub: ", request)
  ### publish data
  payload = json.dumps(request).encode('utf-8')
  if payload==None:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"message": "Json payload cannot be empty."}
    )
  publisher = pubsub_v1.PublisherClient()
  ### publisher will automatically encode the payload with base64
  future = publisher.publish(topic_path, payload)
  response = 'Abnormal event happened when publishing message.'
  try:
    message_id = future.result()
    response = f"Message published with ID: {message_id}."
  except Exception as e:
    response = f"Failed to publish message. Error: {e}."
  print("pubsub response: ", response)
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
  publishers = latestStories.publishers
  category = latestStories.category
  index = latestStories.index
  take = latestStories.take
  prefix = FastAPICache.get_prefix()
  
  ### get data from redis
  all_keys = []
  for publisher_id in publishers:
    key = key_builder(f"{prefix}:category_latest", f"{category}:{publisher_id}")
    all_keys.append(key)
  values = await mget_cache(all_keys)
  
  ### organize the data
  values_filtered = [dict(json.loads(value)) for value in values if value!=None] if values!=None else []
  all_stories = []
  update_time = 0
  for value in values_filtered:
    update_time = value.get('update_time', 0) if update_time < value.get('update_time', 0) else update_time
    stories = value.get('data', [])
    for story in stories:
      published_date = story['published_date']
      published_timestamp = int(datetime.strptime(published_date, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp())
      story['published_timestamp'] = published_timestamp
      all_stories.append(story)
  expire_time = update_time + config.EXPIRE_LATEST_STORIES_TIME
  all_stories = sorted(all_stories, key=lambda x: x['published_timestamp'], reverse=True)  
  all_stories_pagination = all_stories[index: index+take]
  response = dict({
    "update_time": update_time,
    "expire_time": expire_time,
    "num_stories": len(all_stories_pagination),
    "stories": all_stories_pagination
  })
  return response

@app.on_event("startup")
async def startup():
  NAMESPACE = os.environ.get('NAMESPACE', 'dev')
  redis_endpoint = os.environ.get('REDIS_ENDPOINT', 'redis-cache:6379')
  redis = aioredis.from_url(f"redis://{redis_endpoint}", encoding="utf8", decode_responses=True)
  FastAPICache.init(RedisBackendExtend(redis), prefix=f"{NAMESPACE}")