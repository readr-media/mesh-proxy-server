'''
[Note] 
    Built-in middleware in Fastapi can only apply to all the routes in an app.
    As a result, instead using built-in middleware, we develop middlewares by ourselves.
'''
from fastapi import Request, status
import jwt
import os
from datetime import datetime 
import pytz
from src.tool import extract_bearer_token
from src.publisher_cache import get_publisher_cache
from src.performance_monitor import monitor_stage

def verify_token(request: Request):
    uid, error_msg = None, None
    
    ### check the existence of Authroization header, which is jwt_token
    bearer_token = request.headers.get("Authorization", None)
    jwt_token = extract_bearer_token(bearer_token)
    if jwt_token==None:
        error_msg = {
            "status_code": status.HTTP_401_UNAUTHORIZED,
            "content": "Cannot find jwt token."
        }
        return uid, error_msg
    
    ### decode
    try: 
        payload = jwt.decode(jwt_token, os.environ['JWT_SECRET'], algorithms='HS256')
        uid = payload['uid']
    except Exception as e:
        error_msg = {
            "status_code": status.HTTP_401_UNAUTHORIZED,
            "content": str(e)
        }
    return uid, error_msg

async def check_publisher_admin_optimized(publisherId: str, firebaseId: str):
    """優化的發布者管理員檢查"""
    from src.performance_monitor import get_current_monitor
    monitor = get_current_monitor()
    
    try:
        # 監控發布者查詢階段
        if monitor:
            async with monitor_stage(monitor, "publisher_admin_query"):
                publisher_cache = get_publisher_cache()
                publisher = await publisher_cache.get_publisher_admin_info(publisherId)
                
                if publisher and firebaseId == publisher['admin']["firebaseId"]:
                    return publisher
                
    except Exception as e:
        print("check publisher admin error: ", str(e))
    
    return None

def check_story_acl(request: Request):
    '''
        Check jwt_token which is retrieved from /accesstoken. 
        If jwt_token is valid, we dispatch the transactions into the ACL of gql forward header. 
    '''
    import time
    from src.performance_monitor import get_current_monitor
    from src.acl_cache import get_acl_cache, cached_jwt_decode, process_acl_from_payload
    
    acl_header = {}
    
    # 取得當前監控器
    monitor = get_current_monitor()
    
    # 檢查 Authorization header
    bearer_token = request.headers.get("Authorization", None)
    jwt_token = extract_bearer_token(bearer_token)
    if jwt_token == None:
        return acl_header, None

    # 取得 ACL 快取
    acl_cache = get_acl_cache()
    
    # 嘗試從快取取得 ACL
    cached_acl = acl_cache.get(jwt_token)
    if cached_acl is not None:
        if monitor:
            monitor.add_stage("acl_cache_hit", 0.001)  # 快取命中
        return cached_acl, None
    
    # 監控 JWT 解碼階段
    if monitor:
        jwt_start = time.time()
    
    try:
        # 使用快取的 JWT 解碼
        payload = cached_jwt_decode(jwt_token, os.environ['JWT_SECRET'])
        
        if monitor:
            monitor.add_stage("jwt_decoding", time.time() - jwt_start)
        
        # 監控 ACL 處理階段
        if monitor:
            acl_start = time.time()
        
        # 處理 ACL
        acl_header = process_acl_from_payload(payload)
        
        # 快取結果
        acl_cache.set(jwt_token, acl_header)
        
        if monitor:
            monitor.add_stage("acl_processing", time.time() - acl_start)
            
    except Exception as e:
        print("middleware_story_acl error: ", e)
        if monitor:
            monitor.add_stage("jwt_decoding", time.time() - jwt_start)
        return acl_header, None
    
    return acl_header, None 