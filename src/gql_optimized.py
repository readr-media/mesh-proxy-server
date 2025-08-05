# 確保 JSON 優化生效
import src.json_optimizer
import json
from typing import Optional, Dict, Any, Tuple
from src.http_client import get_http_client
import src.config as config

async def gql_query_optimized(gql_endpoint: str, gql_string: str = None, gql_variables: str = None, operation_name: str = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    優化的 GQL 查詢函數，使用 HTTP 連接池
    """
    json_data, error_message = None, None
    
    try:
        # 準備 GraphQL 請求資料
        request_data = {
            "query": gql_string
        }
        
        if gql_variables:
            request_data["variables"] = gql_variables
            
        if operation_name:
            request_data["operationName"] = operation_name
        
        # 使用優化的 HTTP 客戶端
        http_client = await get_http_client()
        json_data = await http_client.post_json(gql_endpoint, request_data)
        
    except Exception as e:
        print("GQL query error:", e)
        error_message = str(e)
    
    return json_data, error_message

# 複製原有的預定義查詢
gql_stories = """
query Stories{{
  stories(where: {{source: {{id: {{equals: {ID} }} }} }}, take: {TAKE}, orderBy: {{published_date: desc}} ){{
    id
    title
    source{{
      id
      title
    }}
    url
    summary
    content
  }}
}}
"""

gql_transactions = """
query transactions{{
  transactions(
    where: {{
      member: {{
        firebaseId: {{
          equals: \"{FIREBASE_ID}\"
        }}
      }},
      active: {{
        equals: true
      }},
      status: {{
        equals: Success
      }}
    }}){{
    id
    policy{{
      type
      unlockSingle
      publisher{{
        id
        title
      }}
    }}
    tid
    unlockStory{{
      id
    }}
    expireDate
  }}
}}
"""

gql_all_publishers = """
query Publishers{
  publishers{
    id
    title
    customId
  }
}
"""

gql_publisher_admin = """
query publisher{{
  publisher(where: {{id: {ID} }}){{
    customId
    admin{{
      firebaseId
    }}
  }}
}}
"""

gql_member_firebaseId = """
query member{{
  member(where: {{firebaseId: {ID} }}){{
    id
    firebaseId
  }}
}}
"""

gql_invitation_codes = """
query invitationCodes{{
  invitationCodes(
    where: {{
      member: {{
        firebaseId: {{
          equals: {MEMBER_FIREBASE_ID}
        }}
      }}
    }}
  ){{
    id
    code
    status
  }}
}}
"""

gql_create_codes = """
mutation createInvitationCodes{{
  createInvitationCodes(
    data: {{
      member: {{
        connect: {{
          firebaseId: {MEMBER_FIREBASE_ID}
        }}
      }}
      count: {COUNT}
    }}
  ){{
    id
    code
    status
  }}
}}
""" 