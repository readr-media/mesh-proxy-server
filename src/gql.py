from gql.transport.requests import RequestsHTTPTransport
from gql import gql, Client
from pydantic import BaseModel, ConfigDict
import src.config as config 

import requests
import httpx

async def proxy_request(url: str, data: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()

def gql_query_forward(gql_endpoint, json_payload: str):
  '''
    forward json_payload to gql_endpoint directly
  '''
  json_data, error_message = None, None
  headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
  try:
    response = requests.post(gql_endpoint, json=json_payload, headers=headers)
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
    gql_client = Client(transport=gql_transport,
                        fetch_schema_from_transport=True)
    json_data = gql_client.execute(gql(gql_string), variable_values=gql_variables, operation_name=operation_name)
  except Exception as e:
    print("GQL query error:", e)
    error_message = e
  return json_data, error_message

class Query(BaseModel):
  # model_config = ConfigDict(extra='allow')
  query: str
  operationName: str = None
  variables: dict = None
  ttl: int = config.DEFAULT_GQL_TTL
  
class Forward(BaseModel):
  model_config = ConfigDict(extra='allow')

class LatestStories(BaseModel):
  publishers: list[str] = []
  
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