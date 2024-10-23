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

def middleware_verify_token(request: Request):
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

def middleware_story_acl(request: Request):
    '''
        Check jwt_token which is retrieved from /accesstoken. 
        If jwt_token is valid, we dispatch the transactions into the ACL of gql forward header. 
    '''
    acl_header, error_msg = {}, None
    unix_current = int(datetime.now(pytz.timezone('Asia/Taipei')).timestamp())
    
    ### check the existence of Authroization header, which is jwt_token
    bearer_token = request.headers.get("Authorization", None)
    jwt_token = extract_bearer_token(bearer_token)
    if jwt_token==None:
        error_msg = "Cannot find jwt token."
        return acl_header, error_msg

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