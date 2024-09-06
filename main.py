from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from src.backend.redis import RedisBackendExtend
from redis import asyncio as aioredis

from src.request_body import LatestStories, GqlQuery
import src.auth as Authentication
import src.proxy as proxy
from src.search import search_related_stories
from src.middleware import middleware_story_acl
from src.tool import extract_bearer_token
import src.config as config

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
  return dict(message="Health check for mesh-proxy-server")

@app.post('/accesstoken')
async def accesstoken(request: Request):
  bearer_token = (request.headers.get("Authorization", None) or request.cookies.get('Authorization', None))
  jwt_token = extract_bearer_token(bearer_token)
  if not jwt_token:
    return JSONResponse(
      status_code=status.HTTP_401_UNAUTHORIZED,
      content={"message": "Token is missing or wrong."}
    )
  
  uid, error_message = Authentication.verifyIdToken(jwt_token)
  if error_message:
    return JSONResponse(
      status_code=status.HTTP_401_UNAUTHORIZED,
      content={"message": f"verifyIdToken failed. {error_message}"}
    )
  jwt_token = Authentication.generate_jwt_token(uid)
  if jwt_token==None:
    return JSONResponse(
      status_code=status.HTTP_401_UNAUTHORIZED,
      content={"message": "Failed to generate jwt token."}
    )
  return JSONResponse(
    status_code=status.HTTP_200_OK,
    content={"token": jwt_token}
  )

@app.post('/pubsub')
async def pubsub(request: dict):
  '''
  Forward pubsub messages
  '''
  ### categorize pubsub into different topics
  action = request.get('action', '')
  action_type = 'user_action'
  for topic, actions in config.PUBSUB_TOPIC_ACTIONS.items():
    if action in actions:
      action_type = topic
  print(f"pubsub action {action} matches action_type {action_type}")
    
  ### forward pubsub messages
  payload = json.dumps(request).encode('utf-8')
  if payload==None:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"message": "Json payload cannot be empty."}
    )
  response = proxy.pubsub_proxy(payload, action_type)
  print("pubsub response: ", response)
  return dict({"message": response})

@app.post('/gql')
async def gql(request: Request):
  '''
  Forward gql request by http method without cache.
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  acl_header, error_msg = middleware_story_acl(request)
  if error_msg:
    return JSONResponse(
      status_code=status.HTTP_401_UNAUTHORIZED,
      content={"message": f"{error_msg}"}
    )
  response, error_msg = await proxy.gql_proxy_raw(gql_endpoint, request, acl_header)
  if error_msg:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"message": f"{error_msg}"}
    )
  return dict(response)

@app.post('/gql/cache')
async def forward(request: GqlQuery):
  '''
  Forward gql request by http method with cache.
  '''
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  gql_payload = request.model_dump()
  
  response, error_message = await proxy.gql_proxy_with_cache(gql_endpoint, gql_payload)
  if error_message:
    return JSONResponse(
      status_code=status.HTTP_400_BAD_REQUEST,
      content={"message": f"{error_message}"}
    )
  return dict(response)

@app.post('/latest_stories')
async def latest_stories(latestStories: LatestStories):
  '''
  Get latest stories by publisher ids.
  '''
  response = await proxy.latest_stories_proxy(latestStories)
  return response

@app.get('/search/{search_text}')
@cache(expire=config.SEARCH_EXPIRE_TIME)
async def search(search_text: str):
  print("search_text is: ", search_text)
  related_stories = search_related_stories(search_text)
  return related_stories

@app.on_event("startup")
async def startup():
  ### initialize redis and fastapi cache
  NAMESPACE = os.environ.get('NAMESPACE', 'dev')
  redis_endpoint = os.environ.get('REDIS_ENDPOINT', 'redis-cache:6379')
  redis = aioredis.from_url(f"redis://{redis_endpoint}", encoding="utf8", decode_responses=True)
  FastAPICache.init(RedisBackendExtend(redis), prefix=f"{NAMESPACE}")
  
  ### initialize firebase
  Authentication.initFirebaseAdmin()