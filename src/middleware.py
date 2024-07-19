'''
[Note] 
    Built-in middleware in Fastapi can only apply to all the routes in an app.
    As a result, instead using built-in middleware, we develop middlewares by ourselves.
'''
from src.accesstoken import verify_jwt_token
import json
from fastapi import Request

def middleware_story_acl(request: Request):
    '''
        Check jwt_token which is retrieved from /accesstoken. 
        If jwt_token is valid, we dispatch the transactions into the ACL of gql forward header. 
    '''
    acl_header, error_msg = None, None
    
    ### check the existence of Authroization header, which is jwt_token
    jwt_token = request.headers.get("Authorization", None)
    if jwt_token==None:
        return acl_header, error_msg
    
    try:
        ### if jwt_token is invalid, this line will cause exception
        jwt_token = json.loads(jwt_token)
        ### check the content in the jwt_token
        result = verify_jwt_token(jwt_token)
        if result==False:
            error_msg = "Invalid jwt token"
            return acl_header, error_msg
        
        ### unwrap transactions from jwt_token['claim'] and wrap them into acl_header
        txs = jwt_token.get('claim', {}).get('txs', []) # txs = transacions
        unlock_all_txs, unlock_media_txs, unlock_single_txs = [], [], []
        # categorize all the transactions
        for tx in txs:
            policy_type = tx.get('policy',{}).get('type', '')
            unlockSingle = tx.get('policy', {}).get('unlockSingle', False)
            if policy_type == 'unlock_all_publishers':
                unlock_all_txs.append(tx)
            if policy_type == 'unlock_one_publisher':
                if unlockSingle==False:
                    unlock_media_txs.append(tx)
                else:
                    unlock_single_txs.append(tx)
        # wrap acl header
        if len(unlock_all_txs)>0:
            acl_header = {
                "x-access-token-scope": "mesh:member-stories:all"
            }
        else:
            mediaArr = [tx.get('policy', {}).get('publisher', {}).get('id') for tx in unlock_media_txs]
            mediaArr_str = ','.join(mediaArr)
            storyArr = [tx.get('unlockStory',{}).get('id') for tx in unlock_single_txs]
            storyArr_str = ','.join(storyArr)
            acl_header = {
                "x-access-token-scope": "mesh:member-stories:media",
                "x-access-token-media": mediaArr_str,
                "x-access-token-story": storyArr_str,
            }
    except Exception as e:
        print("middleware_story_acl error: ", e)
        return None, None
    return acl_header, None