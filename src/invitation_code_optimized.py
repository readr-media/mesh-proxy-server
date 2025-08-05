import os
import hashlib
import time
import string
import random
from fastapi import status
from src.http_client import get_http_client
from src.performance_monitor import monitor_stage

gql_invitation_codes = '''
query($where: InvitationCodeWhereInput!){
  invitationCodes(where: $where){
    code
  }
}
'''

gql_member_firebaseId = '''
query member{{
    member(where: {{ firebaseId: {ID} }}){{
      id
    }}
}}
'''

gql_create_codes = '''
mutation($data: [InvitationCodeCreateInput!]!){
  createInvitationCodes(data: $data){
    id
    code
  }
}
'''

async def generate_codes_optimized(uid: str, num_codes: int = 5, num_chars: int = 6):
    """優化的邀請碼生成函數"""
    from src.performance_monitor import get_current_monitor
    monitor = get_current_monitor()
    
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    current_time = str(time.time())
    codes, error_msg = None, None
    
    try:
        # 監控成員查詢階段
        if monitor:
            async with monitor_stage(monitor, "member_query"):
                http_client = await get_http_client()
                query = gql_member_firebaseId.format(ID=f'"{uid}"')
                data, _ = await http_client.post_json(MESH_GQL_ENDPOINT, {"query": query}, {})
                
                if data.get('data', {}).get('member', None) == None:
                    raise Exception('Member not found')
                member_id = data['data']['member']['id']
        
        # 監控邀請碼生成階段
        if monitor:
            async with monitor_stage(monitor, "code_generation"):
                # generate hash value by sha256, number of codes generated is 2*num_codes
                # which is greater than num_codes because of preventing duplicated codes
                member_str = uid + current_time
                random_seeds = [str(random.randint(1, 10000)) for _ in range(num_codes*2)]
                encode_strs = [member_str+rseed for rseed in random_seeds]

                codes = []
                for estr in encode_strs:
                    hash_object = hashlib.sha256(estr.encode())
                    hex_dig = hash_object.hexdigest() # to hexdigest
                    base62_chars = string.ascii_letters + string.digits # using base64 to transform to letter and digits
                    base62_hash = ''.join(base62_chars[int(hex_dig[i:i+2], 16) % 62] for i in range(0, len(hex_dig), 2))
                    codes.append(base62_hash[:num_chars])
        
        # 監控重複檢查階段
        if monitor:
            async with monitor_stage(monitor, "duplicate_check"):
                # search existed codes
                gql_mutation = {
                    "where": {
                        "code": {
                            "in": codes
                        }
                    }
                }
                existed_codes, _ = await http_client.post_json(
                    MESH_GQL_ENDPOINT, 
                    {"query": gql_invitation_codes, "variables": gql_mutation}, 
                    {}
                )
                existed_codes = existed_codes['data']['invitationCodes']
                diff_codes = []
                for code_pair in existed_codes:
                    diff_codes.append(code_pair['code'])

                # filter out duplicated codes
                inserted_codes = set(codes).difference(set(diff_codes))
                inserted_codes = list(inserted_codes)[:num_codes]
        
        # 監控邀請碼創建階段
        if monitor:
            async with monitor_stage(monitor, "code_creation"):
                # insert into cms
                mutation_list = [{
                    "code": code,
                    "send": {
                        "connect": {
                            "id": member_id
                        }
                    }
                } for code in inserted_codes]
                
                gql_mutation = {
                    "data": mutation_list
                }
                codes, _ = await http_client.post_json(
                    MESH_GQL_ENDPOINT, 
                    {"query": gql_create_codes, "variables": gql_mutation}, 
                    {}
                )
                if codes.get('data', {}).get('createInvitationCodes', None) == None:
                    raise Exception('Failed to create invitation codes')
                codes = codes['data']['createInvitationCodes']
                
    except Exception as e:
        print("Generate invitation code error:", e)
        error_msg = {
            "status_code": status.HTTP_400_BAD_REQUEST,
            "content": str(e)
        }
    return codes, error_msg 