from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportError
from gql import gql, Client
from pydantic import BaseModel

def gql_query(gql_endpoint, gql_string, gql_variable: None):
    '''
        gql_fetch is used to retrieve data
    '''
    json_data = None
    try:
      gql_transport = RequestsHTTPTransport(url=gql_endpoint)
      gql_client = Client(transport=gql_transport,
                          fetch_schema_from_transport=True)
      if gql_variable:
        json_data = gql_client.execute(gql(gql_string), variable_values=gql_variable)
      else:
        json_data = gql_client.execute(gql(gql_string))
    except TransportError as e:
      print("Transport Error:", e)
    return json_data

class Query(BaseModel):
  query: str
  variable: str = None
  ttl: int=60

class Response(BaseModel):
  response: dict