from src.gql import gql_query
from src.config import INVITATION_CODE_CHARS, INVITATION_CODE_NUMS
import time
import os
import hashlib
import time
import string
import random
from fastapi import status

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

def generate_codes(uid: str, num_codes: int=INVITATION_CODE_NUMS, num_chars: int=INVITATION_CODE_CHARS): 
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    current_time = str(time.time())
    codes, error_msg = None, None
    
    try:
        data, _ = gql_query(MESH_GQL_ENDPOINT, gql_member_firebaseId.format(ID=f'"{uid}"'))
        if data.get('member', None)==None:
            raise Exception('Member not found')
        member_id = data['member']['id']
        
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
            
        # search existed codes
        gql_mutation = {
            "where": {
                "code": {
                    "in": codes
                }
            }
        }
        existed_codes, _ = gql_query(MESH_GQL_ENDPOINT, gql_invitation_codes, gql_mutation)
        existed_codes = existed_codes['invitationCodes']
        diff_codes = []
        for code_pair in existed_codes:
            diff_codes.append(code_pair['code'])

        # filter out duplicated codes
        inserted_codes = set(codes).difference(set(diff_codes))
        inserted_codes = list(inserted_codes)[:num_codes]
        
        # insert into cms
        mutation_list = [{
            "code": code,
            "send": {
                "connect": {
                    "id": member_id
                }
            }
        } for code in codes]
        
        gql_mutation = {
            "data": mutation_list
        }
        codes, _ = gql_query(MESH_GQL_ENDPOINT, gql_create_codes, gql_mutation)
        if codes.get('createInvitationCodes', None)==None:
            raise Exception('Failed to create invitation codes')
        codes = codes['createInvitationCodes']
    except Exception as e:
        print("Generate invitation code error:", e)
        error_msg = {
            "status_code": status.HTTP_400_BAD_REQUEST,
            "content": str(e)
        }
    return codes, error_msg
    