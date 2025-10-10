from fastapi import FastAPI, status, Request, Path, Depends, Header, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from fastapi_cache import FastAPICache
from src.backend.redis import RedisBackendExtend
from redis import asyncio as aioredis
from typing import Annotated

from src.request_body import LatestStories, SocialPage, Search, Notification
import src.auth as Authentication
import src.proxy as proxy
import src.search as search_api
import src.middleware as middleware
from src.tool import extract_bearer_token, decode_bearer_token, sign_cookie
from src.socialpage import getSocialPage, connect_db
from src.invitation_code import generate_codes
import src.config as config
from src.notify import get_notifies
from src.log import send_search_logging, send_performance_logging
from src.performance_monitor import monitor_stage, log_performance_detailed_async
from src.log import send_logging_async

import os
import json
from datetime import datetime, timedelta, timezone

### App related variables
app = FastAPI()
bearer_scheme = HTTPBearer(auto_error=False)

### API Design
@app.get('/')
async def health_checking():
  return dict(message="Health check for mesh-proxy-server")

@app.get('/diagnostic')
async def diagnostic():
  """
  診斷端點，用於檢查 MongoDB 連接和資料獲取狀態
  """
  from src.diagnostic_middleware import DiagnosticMiddleware
  result = await DiagnosticMiddleware.run_full_diagnostic()
  return result

@app.get('/diagnostic/mongo')
async def diagnostic_mongo():
  """
  僅檢查 MongoDB 連接狀態
  """
  from src.diagnostic_middleware import DiagnosticMiddleware
  result = await DiagnosticMiddleware.check_mongo_connection()
  return result

@app.post('/accesstoken')
async def accesstoken(request: Request):
  start_time = datetime.now().timestamp()
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
  
  # log performance
  end_time = datetime.now().timestamp()
  send_performance_logging({
    "endpoint": "POST: /accesstoken",
    "execute_time": end_time - start_time
  })
  
  return JSONResponse(
    status_code=status.HTTP_200_OK,
    content={"token": jwt_token}
  )

@app.post('/pubsub')
async def pubsub(request: dict):
  '''
  Forward pubsub messages
  '''
  start_time = datetime.now().timestamp()
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
  
  ### log performance
  end_time = datetime.now().timestamp()
  send_performance_logging({
    "endpoint": "POST: /pubsub",
    "execute_time": end_time - start_time
  })
  return dict({"message": response})

@app.post('/gql')
async def gql(request: Request):
  '''
  Forward gql request by http method without cache.
  '''
  from src.performance_monitor import PerformanceMonitor, log_performance_detailed_async, set_current_monitor
  
  # 建立效能監控器
  monitor = PerformanceMonitor("POST: /gql")
  monitor.start()
  set_current_monitor(monitor)
  
  try:
    gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
    
    # 監控 ACL 檢查階段
    async with monitor_stage(monitor, "acl_check"):
      acl_header, error_msg = middleware.check_story_acl(request)
      if error_msg:
        return JSONResponse(
          status_code=status.HTTP_401_UNAUTHORIZED,
          content={"message": f"{error_msg}"}
        )
    
    # 監控 GQL 代理階段
    async with monitor_stage(monitor, "gql_proxy"):
      response, error_msg = await proxy.gql_proxy_raw(gql_endpoint, request, acl_header)
      if error_msg:
        return JSONResponse(
          status_code=status.HTTP_400_BAD_REQUEST,
          content={"message": f"{error_msg}"}
        )
    
    # 監控回應處理階段
    async with monitor_stage(monitor, "response_handling"):
      try:
        request_data = await request.json()
      except:
        request_data = None
      
      # 記錄詳細效能資訊
      monitor.end()
      await log_performance_detailed_async(monitor)
      
      # 同時保留原本的簡化日誌（非同步）
      await send_logging_async(
        os.environ.get('PROJECT_ID'),
        os.environ.get('LOG_NAME_PERFORMANCE', 'performance'),
        {
          "endpoint": "POST: /gql",
          "execute_time": monitor.get_total_duration(),
          "data": request_data,
        }
      )
    
    return dict(response)
    
  finally:
    # 清理監控器
    set_current_monitor(None)

@app.post('/latest_stories')
async def latest_stories(latestStories: LatestStories):
  '''
  Get latest stories by publisher ids.
  '''
  start_time = datetime.now().timestamp()
  response = await proxy.latest_stories_proxy(latestStories)
  # log performance
  end_time = datetime.now().timestamp()
  send_performance_logging({
    "endpoint": "POST: /latest_stories",
    "execute_time": end_time - start_time,
    "data": latestStories.model_dump(),
  })
  return response

@app.api_route('/search', methods=['GET', 'POST'])
async def search_endpoint(
  request: Request,
  search: Search = None,
  text: str = None,
  objectives: str = "story",
  manual: bool = False,
  num: int = 10
):
  start_time = datetime.now().timestamp()
  
  # 根據請求方法處理參數
  if request.method == "POST":
    # POST 請求：使用 JSON body
    search_text = search.text
    objectives_list = search.objectives
    manual = search.manual
    num = search.num
    endpoint_name = "POST: /search"
  else:
    # GET 請求：使用 URL 參數
    search_text = text
    objectives_list = [obj.strip() for obj in objectives.split(',')]
    endpoint_name = "GET: /search"
  
  # 使用效能監控器
  from src.performance_monitor import PerformanceMonitor, log_performance_detailed_async
  monitor = PerformanceMonitor(endpoint_name)
  monitor.start()
  
  try:
    # 使用優化的搜尋函數
    from src.search_optimized import search_all_optimized
    related_data = await search_all_optimized(search_text, objectives_list, monitor=monitor)
    
    # 記錄效能資訊
    monitor.end()
    await log_performance_detailed_async(monitor)
    
    # cloud logging
    end_time = datetime.now().timestamp()
    search_data = Search(text=search_text, objectives=objectives_list, manual=manual, num=num)
    send_search_logging(search_data)
    send_performance_logging({
      "endpoint": endpoint_name,
      "execute_time": end_time - start_time,
      "data": search_data.model_dump(),
    })
    
    return related_data
    
  except Exception as e:
    # 記錄錯誤並返回診斷信息
    error_msg = f"搜尋失敗: {str(e)}"
    print(error_msg)
    
    # 嘗試提供診斷信息
    try:
      from src.diagnostic_middleware import DiagnosticMiddleware
      mongo_status = await DiagnosticMiddleware.check_mongo_connection()
      return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
          "error": error_msg,
          "diagnostic": {
            "mongo_connection": mongo_status,
            "search_text": search_text,
            "objectives": objectives_list,
            "suggestion": "請檢查 /diagnostic 端點獲取詳細診斷信息"
          }
        }
      )
    except:
      return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": error_msg}
      )

@app.post('/socialpage')
async def socialpage_pagination(socialPage: SocialPage, nocache: bool = False):
  '''
  Given member_id, return social_page based on index and take
  '''
  start_time = datetime.now().timestamp()
  member_id = socialPage.member_id
  index     = socialPage.index
  take      = socialPage.take
  
  try:
    # 使用優化的社交頁面函數
    from src.socialpage_optimized import getSocialPage_optimized
    print(f"[py/socialpage] route nocache={nocache}")
    socialpage = await getSocialPage_optimized(member_id=member_id, index=index, take=take, nocache=nocache)
    
    # log performance
    end_time = datetime.now().timestamp()
    send_performance_logging({
      "endpoint": "POST: /socialpage",
      "execute_time": end_time - start_time,
      "data": socialPage.model_dump(),
    })
    return socialpage
    
  except Exception as e:
    # 記錄錯誤並返回診斷信息
    error_msg = f"社交頁面獲取失敗: {str(e)}"
    print(error_msg)
    
    # 嘗試提供診斷信息
    try:
      from src.diagnostic_middleware import DiagnosticMiddleware
      mongo_status = await DiagnosticMiddleware.check_mongo_connection()
      return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
          "error": error_msg,
          "diagnostic": {
            "mongo_connection": mongo_status,
            "member_id": member_id,
            "suggestion": "請檢查 /diagnostic 端點獲取詳細診斷信息"
          }
        }
      )
    except:
      return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": error_msg}
      )

@app.post('/invitation_codes/{num_codes}')
async def generate_invitation_codes(
    request: Request, 
    num_codes: Annotated[int, Path(title="Number of codes to be generated", ge=1)]
  ):
  uid, error_msg = middleware.verify_token(request)
  if error_msg:
    return JSONResponse(
      status_code = error_msg['status_code'],
      content = {"message": error_msg['content']}
    )
  codes, error_msg = generate_codes(uid, num_codes)
  if error_msg:
    return JSONResponse(
      status_code = error_msg['status_code'],
      content = {"message": error_msg['content']}
    )
  return codes

@app.post('/notifications')
async def notifications(request: Notification):
  start_time = datetime.now().timestamp()
  memberId = request.member_id
  index = request.index
  take = request.take
  
  try:
    # 使用優化的通知函數
    from src.notify_optimized import get_notifies_optimized
    notifies = await get_notifies_optimized(memberId=memberId, index=index, take=take)
    
    # log performance
    end_time = datetime.now().timestamp()
    send_performance_logging({
      "endpoint": "POST: /notifications",
      "execute_time": end_time - start_time,
      "data": request.model_dump(),
    })
    return notifies
    
  except Exception as e:
    # 記錄錯誤並返回診斷信息
    error_msg = f"通知獲取失敗: {str(e)}"
    print(error_msg)
    
    # 嘗試提供診斷信息
    try:
      from src.diagnostic_middleware import DiagnosticMiddleware
      mongo_status = await DiagnosticMiddleware.check_mongo_connection()
      return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
          "error": error_msg,
          "diagnostic": {
            "mongo_connection": mongo_status,
            "member_id": memberId,
            "suggestion": "請檢查 /diagnostic 端點獲取詳細診斷信息"
          }
        }
      )
    except:
      return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": error_msg}
      )

@app.options('/media/cookie/{publisherId}')
async def preflight_media_cookie(origin: Annotated[str | None, Header()] = None):
  headers = {
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Origin": origin or "*", 
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Authorization, Content-Type",
  }
  return Response(status_code=status.HTTP_204_NO_CONTENT, headers=headers)

@app.get('/media/cookie/{publisherId}')
async def media_cookie(
    publisherId: str, 
    origin: Annotated[str | None, Header()] = None, 
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
  ):
  start_time = datetime.now().timestamp()
  signedcookie_url_prefix = os.environ['SIGNEDCOOKIE_URL_PREFIX']
  signedcookie_key_name = os.environ['SIGNEDCOOKIE_KEY_NAME']
  signedcookie_base64_key = os.environ['SIGNEDCOOKIE_BASE64_KEY']
  gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
  jwt_secret   = os.environ['JWT_SECRET']
  
  # authenticate credentials
  try:
    if not origin:
      raise(Exception("Origin is missing."))
    token = credentials.credentials
    data = decode_bearer_token(secret=jwt_secret, token=token)
    firebaseId = data['uid']
  except Exception as e:
    return JSONResponse(
      status_code = status.HTTP_401_UNAUTHORIZED,
      content = {"message": f"Authentication failed. {str(e)}"}
    )
  
  # check publisher admin
  publisher = middleware.check_publisher_admin(gql_endpoint, publisherId, firebaseId)
  if publisher==None or ("customId" not in publisher):
    return JSONResponse(
      status_code = status.HTTP_401_UNAUTHORIZED,
      content = {"message": "You are not publisher admin."}
    )
  customId = publisher['customId']
  
  # get signed cookie policy
  expiration_time = datetime.now(timezone.utc) + timedelta(seconds=config.SIGNED_COOKIE_TTL)
  expires_str = expiration_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
  policy = sign_cookie(
    url_prefix = f"{signedcookie_url_prefix}/statements/media/{customId}", 
    key_name = signedcookie_key_name, 
    base64_key = signedcookie_base64_key,
    expiration_time = expiration_time
  )
  domain = str(signedcookie_url_prefix).replace("https://", "")
  setCookie = f"{policy};Domain={domain};Path=/statements/media;SameSite=None;Secure;Expires={expires_str};HttpOnly"
  headers = {
    "Set-Cookie": setCookie,
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET, OPTIONS",
  }
  # logging
  end_time = datetime.now().timestamp()
  send_performance_logging({
    "endpoint": "GET: /media/cookie",
    "execute_time": end_time - start_time,
    "data": {"publisherId": publisherId},
  })
  return JSONResponse(content="Signed cookie is set.", headers=headers)

@app.on_event("startup")
async def startup():
  ### initialize redis and fastapi cache
  NAMESPACE = os.environ.get('NAMESPACE', 'dev')
  redis_endpoint = os.environ.get('REDIS_ENDPOINT', 'redis-cache:6379')
  redis = aioredis.from_url(f"redis://{redis_endpoint}", encoding="utf8", decode_responses=True)
  FastAPICache.init(RedisBackendExtend(redis), prefix=f"{NAMESPACE}")
  
  ### initialize firebase
  Authentication.initFirebaseAdmin()
  
  ### initialize HTTP client
  from src.http_client import get_http_client
  await get_http_client()  # 預先建立 HTTP 會話
  
  ### initialize MongoDB connection pool
  from src.mongo_client import initialize_mongo
  mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
  env = os.environ.get('ENV', 'dev')
  await initialize_mongo(mongo_url, env)
  
  ### initialize HTTP client
  from src.http_client import get_http_client
  await get_http_client()  # 預先建立 HTTP 會話

@app.on_event("shutdown")
async def shutdown():
  ### close HTTP client
  from src.http_client import close_http_client
  await close_http_client()
  
  ### close MongoDB connections
  from src.mongo_client import close_mongo
  await close_mongo()