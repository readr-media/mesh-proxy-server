from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from src.backend.redis import RedisBackendExtend
from redis import asyncio as aioredis

from src.request_body import LatestStories, SocialPage, Search, Notification
import src.auth as Authentication
import src.proxy as proxy
import src.search as search_api
from src.middleware import middleware_story_acl, middleware_verify_token
from src.tool import extract_bearer_token
from src.socialpage import getSocialPage, connect_db
from src.invitation_code import generate_codes
import src.config as config
from src.notify import get_notifies
from src.log import send_search_logging

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

@app.post('/latest_stories')
async def latest_stories(latestStories: LatestStories):
  '''
  Get latest stories by publisher ids.
  '''
  response = await proxy.latest_stories_proxy(latestStories)
  return response

@app.post('/search')
async def search_post(search: Search):
  search_text, objectives = search.text, search.objectives
  related_data = {}
  
  ### search from meilisearch
  client = search_api.connect_meilisearch()
  if "story" in objectives:
    related_data["story"] = await search_api.search_related_stories(client, search_text)
  if "collection" in objectives:
    related_data["collection"] = search_api.search_related_collections(client, search_text)
  if "member" in objectives:
    related_data["member"] = search_api.search_related_members(client, search_text)
  if "publisher" in objectives:
    related_data["publisher"] = search_api.search_related_publishers(client, search_text)
  
  ### cloud logging
  try:
    send_search_logging(search)
  except Exception as e:
    print("send search logging error: ", str(e))
  return related_data

@app.post('/socialpage')
async def socialpage_pagination(socialPage: SocialPage):
  '''
  Given member_id, return social_page based on index and take
  '''
  mongo_url = os.environ['MONGO_URL']
  member_id = socialPage.member_id
  index     = socialPage.index
  take      = socialPage.take
  socialpage = await getSocialPage(mongo_url=mongo_url, member_id=member_id, index=index, take=take)
  return socialpage

@app.post('/invitation_codes')
async def generate_invitation_codes(request: Request):
  uid, error_msg = middleware_verify_token(request)
  if error_msg:
    return JSONResponse(
      status_code = error_msg['status_code'],
      content = {"message": error_msg['content']}
    )
  codes, error_msg = generate_codes(uid)
  if error_msg:
    return JSONResponse(
      status_code = error_msg['status_code'],
      content = {"message": error_msg['content']}
    )
  return codes

@app.post('/notifications')
async def notifications(request: Notification):
  mongo_url = os.environ['MONGO_URL']
  memberId = request.member_id
  index = request.index
  take = request.take
  
  db = connect_db(mongo_url, os.environ.get('ENV', 'dev'))
  notifies = get_notifies(db=db, memberId=memberId, index=index, take=take)
  return notifies

@app.on_event("startup")
async def startup():
  ### initialize redis and fastapi cache
  NAMESPACE = os.environ.get('NAMESPACE', 'dev')
  redis_endpoint = os.environ.get('REDIS_ENDPOINT', 'redis-cache:6379')
  redis = aioredis.from_url(f"redis://{redis_endpoint}", encoding="utf8", decode_responses=True)
  FastAPICache.init(RedisBackendExtend(redis), prefix=f"{NAMESPACE}")
  
  ### initialize firebase
  Authentication.initFirebaseAdmin()