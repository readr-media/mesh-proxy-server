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
from src.gql import gql_query, gql_publisher_admin
from src.performance_monitor import monitor_stage

def check_publisher_admin(gql_endpoint: str, publisherId: str, firebaseId: str):
    response = None
    try:
        data, _ = gql_query(gql_endpoint, gql_publisher_admin.format(ID=publisherId))
        publisher = data['publisher']
        if firebaseId==publisher['admin']["firebaseId"]:
            response = publisher
    except Exception as e:
        print("check publisher admin error: ", str(e))
    return response

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

def check_story_acl(request: Request):
    '''
        Check jwt_token which is retrieved from /accesstoken. 
        If jwt_token is valid, we dispatch the transactions into the ACL of gql forward header. 
    '''
    import time
    from src.performance_monitor import get_current_monitor
    
    acl_header = {}
    unix_current = int(datetime.now(pytz.timezone('Asia/Taipei')).timestamp())
    
    # 取得當前監控器
    monitor = get_current_monitor()
    
    # 監控 JWT 解碼階段
    if monitor:
        # 手動計時，因為這是同步函數
        jwt_start = time.time()
        ### check the existence of Authroization header, which is jwt_token
        bearer_token = request.headers.get("Authorization", None)
        jwt_token = extract_bearer_token(bearer_token)
        if jwt_token==None:
            monitor.add_stage("jwt_decoding", time.time() - jwt_start)
            return acl_header, None

        try:
            ### check the content in the jwt_token
            # jwt.decode will return error code automatically if there is any invalid data in jwt_token
            payload = jwt.decode(jwt_token, os.environ['JWT_SECRET'], algorithms='HS256')
            scope = payload['scope']
            monitor.add_stage("jwt_decoding", time.time() - jwt_start)
            
            # 監控 ACL 處理階段
            acl_start = time.time()
            # wrap acl header
            if scope == 'all':
                acl_header = {
                    "x-access-token-scope": "mesh:member-stories:all"
                }
            else:
                # filter out expired media
                mediaArr = payload.get('media', [])
                mediaArr_filtered = set()
                for media in mediaArr:
                    media_id, media_expireDate = media
                    if media_expireDate < unix_current:
                        continue
                    mediaArr_filtered.add(media_id)
                mediaArr_str = ','.join(list(mediaArr_filtered))
                # filter out expired story
                storyArr = payload.get('story', [])
                storyArr_filtered = set()
                for story in storyArr:
                    story_id, story_expireDate = story
                    if story_expireDate < unix_current:
                        continue
                    storyArr_filtered.add(story_id)
                storyArr_str = ','.join(list(storyArr_filtered))
                # wrap acl header
                acl_header = {
                    "x-access-token-scope": "mesh:member-stories:media",
                    "x-access-token-media": mediaArr_str,
                    "x-access-token-story": storyArr_str,
                }
            monitor.add_stage("acl_processing", time.time() - acl_start)
        except Exception as e:
            print("middleware_story_acl error: ", e)
            monitor.add_stage("jwt_decoding", time.time() - jwt_start)
            return acl_header, None
    else:
        # 如果沒有監控器，使用原本的邏輯
        ### check the existence of Authroization header, which is jwt_token
        bearer_token = request.headers.get("Authorization", None)
        jwt_token = extract_bearer_token(bearer_token)
        if jwt_token==None:
            return acl_header, None

        try:
            ### check the content in the jwt_token
            # jwt.decode will return error code automatically if there is any invalid data in jwt_token
            payload = jwt.decode(jwt_token, os.environ['JWT_SECRET'], algorithms='HS256')
            scope = payload['scope']
            
            # wrap acl header
            if scope == 'all':
                acl_header = {
                    "x-access-token-scope": "mesh:member-stories:all"
                }
            else:
                # filter out expired media
                mediaArr = payload.get('media', [])
                mediaArr_filtered = set()
                for media in mediaArr:
                    media_id, media_expireDate = media
                    if media_expireDate < unix_current:
                        continue
                    mediaArr_filtered.add(media_id)
                mediaArr_str = ','.join(list(mediaArr_filtered))
                # filter out expired story
                storyArr = payload.get('story', [])
                storyArr_filtered = set()
                for story in storyArr:
                    story_id, story_expireDate = story
                    if story_expireDate < unix_current:
                        continue
                    storyArr_filtered.add(story_id)
                storyArr_str = ','.join(list(storyArr_filtered))
                # wrap acl header
                acl_header = {
                    "x-access-token-scope": "mesh:member-stories:media",
                    "x-access-token-media": mediaArr_str,
                    "x-access-token-story": storyArr_str,
                }
        except Exception as e:
            print("middleware_story_acl error: ", e)
            return acl_header, None
    return acl_header, None