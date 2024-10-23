import os
import requests
import json
from google.cloud import pubsub_v1
from fastapi_cache import FastAPICache
import src.config as config
from src.tool import key_builder
from src.cache import get_cache, set_cache, mget_cache
from src.request_body import LatestStories
from datetime import datetime
from fastapi import Request
from starlette.datastructures import UploadFile

def pubsub_proxy(payload, action_type: str='user_action'):
    if action_type == 'payment':
      topic_path = os.environ['PUBSUB_TOPIC_PAYMENT']
    else:
      topic_path = os.environ['PUBSUB_TOPIC_USERACTION']
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

async def gql_proxy_raw(gql_endpoint: str, request: Request, acl_headers: dict):
    content_type = request.headers.get('Content-Type', '')
    json_data, error_message = None, None
    try:
      if 'multipart/form-data' in content_type:
        form = await request.form()
        data, files = {}, {}
        for key, value in form.items():
          if isinstance(value, UploadFile):
            print("gql proxy with upload file")
            files[key] = await value.read()
          else:
            data[key] = value
        response = requests.post(gql_endpoint, data=data, files=files, headers=acl_headers, timeout=config.DEFAULT_GQL_EXEC_TIMEOUT)
      else:
        data = await request.json()
        response = requests.post(gql_endpoint, json=data, headers=acl_headers, timeout=config.DEFAULT_GQL_EXEC_TIMEOUT)
      json_data = response.json()
    except Exception as e:
      print("GQL query error:", e)
      error_message = e
    return json_data, error_message
  
async def latest_stories_proxy(latestStories: LatestStories):
    publishers = latestStories.publishers
    category = latestStories.category
    index = latestStories.index
    take = latestStories.take
    prefix = FastAPICache.get_prefix()
    
    ### get data from redis
    all_keys = []
    for publisher_id in publishers:
      key = key_builder(f"{prefix}:category_latest", f"{category}:{publisher_id}")
      all_keys.append(key)
    values = await mget_cache(all_keys)
    
    ### organize the data
    values_filtered = [dict(json.loads(value)) for value in values if value!=None] if values!=None else []
    all_stories = []
    update_time = 0
    for value in values_filtered:
      update_time = value.get('update_time', 0) if update_time < value.get('update_time', 0) else update_time
      stories = value.get('data', [])
      for story in stories:
        published_date = story['published_date']
        published_timestamp = int(datetime.strptime(published_date, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp())
        story['published_timestamp'] = published_timestamp
        all_stories.append(story)
    expire_time = update_time + config.EXPIRE_LATEST_STORIES_TIME
    all_stories = sorted(all_stories, key=lambda x: x['published_timestamp'], reverse=True)  
    all_stories_pagination = all_stories[index: index+take]
    response = dict({
      "update_time": update_time,
      "expire_time": expire_time,
      "num_stories": len(all_stories),
      "stories": all_stories_pagination
    })
    return response