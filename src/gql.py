from gql.transport.requests import RequestsHTTPTransport
from gql import gql, Client
import requests
import src.config as config

def gql_query_forward(gql_endpoint, json_payload: dict):
  '''
    forward json_payload to gql_endpoint directly
  '''
  json_data, error_message = None, None
  try:
    response = requests.post(gql_endpoint, json=json_payload)
    json_data = response.json()
    print("Return data is: ", json_data)
  except Exception as e:
    print("GQL query error:", e)
    error_message = e
  return json_data, error_message

def gql_query(gql_endpoint, gql_string: str=None, gql_variables: str=None, operation_name: str=None):
  '''
      gql_fetch is used to retrieve data
  '''
  json_data, error_message = None, None
  try:
    gql_transport = RequestsHTTPTransport(url=gql_endpoint)
    gql_client = Client(
      transport=gql_transport,
      fetch_schema_from_transport=True,
      execute_timeout=config.DEFAULT_GQL_EXEC_TIMEOUT
    )
    json_data = gql_client.execute(gql(gql_string), variable_values=gql_variables, operation_name=operation_name)
  except Exception as e:
    print("GQL query error:", e)
    error_message = e
  return json_data, error_message
  
### Predefined gql queries
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