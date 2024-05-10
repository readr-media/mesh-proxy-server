from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportError
from gql import gql, Client

def gql_fetch(gql_endpoint, gql_string):
    '''
        gql_fetch is used to retrieve data
    '''
    json_data = None
    try:
      gql_transport = RequestsHTTPTransport(url=gql_endpoint)
      gql_client = Client(transport=gql_transport,
                          fetch_schema_from_transport=True)
      json_data = gql_client.execute(gql(gql_string))
    except TransportError as e:
      print("Transport Error:", e)
    return json_data
