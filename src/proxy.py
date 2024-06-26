import os
import requests
from google.cloud import pubsub_v1

def pubsub_proxy(payload):
    topic_path = os.environ['PUBSUB_TOPIC']
    publisher = pubsub_v1.PublisherClient()
    ### publisher will automatically encode the payload with base64
    future = publisher.publish(topic_path, payload)
    response = 'Failed to publisher message.'
    try:
        message_id = future.result()
        response = f"Message published with ID: {message_id}."
    except Exception as e:
        response += f" Error: {e}."
    return response

def gql_proxy_without_cache(gql_endpoint, json_payload: dict):
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