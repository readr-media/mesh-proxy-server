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
from src.log import send_performance_logging
from starlette.datastructures import UploadFile
from src.performance_monitor import monitor_stage

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
    import time
    from src.performance_monitor import get_current_monitor
    from src.http_client import get_http_client
    
    content_type = request.headers.get('Content-Type', '')
    json_data, error_message = None, None
    
    # 取得當前監控器
    monitor = get_current_monitor()
    
    try:
      # 監控請求準備階段
      if monitor:
          async with monitor_stage(monitor, "request_preparation"):
              if 'multipart/form-data' in content_type:
                  form = await request.form()
                  data, files = {}, {}
                  for key, value in form.items():
                    if isinstance(value, UploadFile):
                      print("gql proxy with upload file")
                      files[key] = await value.read()
                    else:
                      data[key] = value
              else:
                  data = await request.json()
      
      # 監控網路請求階段
      if monitor:
          async with monitor_stage(monitor, "network_request"):
              http_client = await get_http_client()
              if 'multipart/form-data' in content_type:
                  json_data = await http_client.post_form(gql_endpoint, data, files, acl_headers)
              else:
                  json_data = await http_client.post_json(gql_endpoint, data, acl_headers)
      else:
          # 如果沒有監控器，使用原本的邏輯
          if 'multipart/form-data' in content_type:
              form = await request.form()
              data, files = {}, {}
              for key, value in form.items():
                if isinstance(value, UploadFile):
                  print("gql proxy with upload file")
                  files[key] = await value.read()
                else:
                  data[key] = value
              http_client = await get_http_client()
              json_data = await http_client.post_form(gql_endpoint, data, files, acl_headers)
          else:
              data = await request.json()
              http_client = await get_http_client()
              json_data = await http_client.post_json(gql_endpoint, data, acl_headers)
      
      # 監控回應處理階段
      if monitor:
          async with monitor_stage(monitor, "response_processing"):
              # 回應已經在網路請求階段處理了
              pass
          
    except Exception as e:
      print("GQL query error:", e)
      error_message = e
    return json_data, error_message
  
async def latest_stories_proxy(latestStories: LatestStories):
    start_time = datetime.now()
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
    print(all_keys)
    redis_end_time = datetime.now()
    
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
    organize_end_time = datetime.now()
    expire_time = update_time + config.EXPIRE_LATEST_STORIES_TIME
    all_stories = sorted(all_stories, key=lambda x: x['published_timestamp'], reverse=True)  
    all_stories_pagination = all_stories[index: index+take]
    response = dict({
      "update_time": update_time,
      "expire_time": expire_time,
      "num_stories": len(all_stories),
      "stories": all_stories_pagination
    })
    end_time = datetime.now()
    data = {
        "function": "latest_stories_proxy",
        "stages": [
          {
            "name": "get data from redis",
            "start_time": str(start_time),
            "end_time": str(redis_end_time),
            "duration": (redis_end_time - start_time).total_seconds()
          },
          {
            "name": "organize the data",
            "start_time": str(redis_end_time),
            "end_time": str(organize_end_time),
        "end_time": str(end_time),
        "duration": (end_time - start_time).total_seconds()
          }
        ]
    }
    send_performance_logging(data)
    return response