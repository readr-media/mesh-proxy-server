import meilisearch
import os
import asyncio
import src.config as config
from src.gql_optimized import gql_query_optimized

from fastapi_cache import FastAPICache
from src.cache import get_cache, set_cache
from src.tool import key_builder
import json
from typing import Dict, List, Any, Optional
from src.performance_monitor import PerformanceMonitor, monitor_stage

# GraphQL 查詢保持不變
gql_story_search = '''
query Stories($where: StoryWhereInput!){
  stories(where: $where){
    id
    title
    og_image
    og_description
    published_date
    full_screen_ad
    isMember
    source{
      id
      customId
      title
      is_active
    }
  }
}
'''

gql_collection_search = '''
query Collections($where: CollectionWhereInput!){
  collections(where: $where){
    id
    title
    status
    creator{
      id
      customId
      nickname
      name
    }
    heroImage{
      resized{
        original
      }
      urlOriginal
    }
    readsCount: picksCount(
      where: {
        is_active: {
          equals: true
        }
      }
    )
  }
}
'''

gql_member_search = '''
query Members($where: MemberWhereInput!){
    members(where: $where){
        id
        name
        nickname
        customId
        avatar
        is_active
    }
}
'''

# 全域 MeiliSearch 客戶端實例
_meilisearch_client: Optional[meilisearch.Client] = None

def get_meilisearch_client() -> meilisearch.Client:
    """取得全域 MeiliSearch 客戶端實例，避免重複建立連接"""
    global _meilisearch_client
    if _meilisearch_client is None:
        MEILISEARCH_HOST = os.environ['MEILISEARCH_HOST']
        MEILISEARCH_APIKEY = os.environ['MEILISEARCH_APIKEY']
        _meilisearch_client = meilisearch.Client(MEILISEARCH_HOST, MEILISEARCH_APIKEY)
    return _meilisearch_client

def ranking_result(sequence: list, content_table: dict):
    '''
    Sequence is the list of story[id] sorted by ranking score from high to low.
    We follow the sequence and retrieve full story from content_table
    '''
    result = []
    for id in sequence:
        content = content_table.get(str(id), None)
        if content:
            result.append(content)
    return result

async def search_related_stories_optimized(
    search_text: str, 
    num: int = config.MEILISEARCH_RELATED_STORIES_NUM,
    monitor: Optional[PerformanceMonitor] = None
) -> List[Dict[str, Any]]:
    '''
    優化的故事搜尋函數，包含並行處理和快取優化
    '''
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    related_stories = []
    
    try:
        # 檢查快取
        if monitor:
            async with monitor_stage(monitor, "cache_check"):
                prefix = FastAPICache.get_prefix()
                key = key_builder(f"{prefix}:search_stories", search_text)
                _, cached_data = await get_cache(key)
                if cached_data:
                    return json.loads(cached_data)
        else:
            prefix = FastAPICache.get_prefix()
            key = key_builder(f"{prefix}:search_stories", search_text)
            _, cached_data = await get_cache(key)
            if cached_data:
                return json.loads(cached_data)

        # MeiliSearch 搜尋
        if monitor:
            async with monitor_stage(monitor, "meilisearch_search"):
                client = get_meilisearch_client()
                search_stories = client.index(config.MEILISEARCH_STORY_INDEX).search(search_text, {
                    'attributesToRetrieve': ['id', 'title'],
                    'limit': num
                })['hits']
        else:
            client = get_meilisearch_client()
            search_stories = client.index(config.MEILISEARCH_STORY_INDEX).search(search_text, {
                'attributesToRetrieve': ['id', 'title'],
                'limit': num
            })['hits']

        # 取得完整資訊
        if monitor:
            async with monitor_stage(monitor, "gql_fetch"):
                search_ids = [story['id'] for story in search_stories]
                search_var = {
                    "where": {
                        "id": {
                            "in": search_ids
                        }
                    }
                }
                stories, err = await gql_query_optimized(MESH_GQL_ENDPOINT, gql_story_search, search_var)
        else:
            search_ids = [story['id'] for story in search_stories]
            search_var = {
                "where": {
                    "id": {
                        "in": search_ids
                    }
                }
            }
            stories, err = await gql_query_optimized(MESH_GQL_ENDPOINT, gql_story_search, search_var)

        if err is None and isinstance(stories, dict):
            stories = stories['stories']
        else:
            raise Exception(str(err))

        # 後處理過濾
        if monitor:
            async with monitor_stage(monitor, "post_processing"):
                content_table = {}
                for story in stories:
                    id = story.get('id', None)
                    source = story.get('source', None)
                    if id is None or source is None or not isinstance(source, dict):
                        continue
                    source_is_active = source.get('is_active', False)
                    if not source_is_active:
                        continue
                    content_table[id] = story
                
                # 排序相關故事
                related_stories = ranking_result(search_ids, content_table)
        else:
            content_table = {}
            for story in stories:
                id = story.get('id', None)
                source = story.get('source', None)
                if id is None or source is None or not isinstance(source, dict):
                    continue
                source_is_active = source.get('is_active', False)
                if not source_is_active:
                    continue
                content_table[id] = story
            
            related_stories = ranking_result(search_ids, content_table)

        # 設定快取
        if monitor:
            async with monitor_stage(monitor, "cache_set"):
                await set_cache(key, json.dumps(related_stories), ttl=config.SEARCH_STORY_CACHE_TTL)
        else:
            await set_cache(key, json.dumps(related_stories), ttl=config.SEARCH_STORY_CACHE_TTL)

    except Exception as e:
        print("Search related stories error:", e)
        
    return related_stories

async def search_related_collections_optimized(
    search_text: str, 
    num: int = config.MEILISEARCH_RELATED_COLLECTIONS_NUM,
    monitor: Optional[PerformanceMonitor] = None
) -> List[Dict[str, Any]]:
    '''
    優化的集合搜尋函數
    '''
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    related_collections = []
    
    try:
        # 檢查快取
        if monitor:
            async with monitor_stage(monitor, "cache_check"):
                prefix = FastAPICache.get_prefix()
                key = key_builder(f"{prefix}:search_collections", search_text)
                _, cached_data = await get_cache(key)
                if cached_data:
                    return json.loads(cached_data)
        else:
            prefix = FastAPICache.get_prefix()
            key = key_builder(f"{prefix}:search_collections", search_text)
            _, cached_data = await get_cache(key)
            if cached_data:
                return json.loads(cached_data)

        # MeiliSearch 搜尋
        if monitor:
            async with monitor_stage(monitor, "meilisearch_search"):
                client = get_meilisearch_client()
                search_stories = client.index(config.MEILISEARCH_COLLECTION_INDEX).search(search_text, {
                    'limit': num
                })['hits']
        else:
            client = get_meilisearch_client()
            search_stories = client.index(config.MEILISEARCH_COLLECTION_INDEX).search(search_text, {
                'limit': num
            })['hits']

        # 取得完整資訊
        if monitor:
            async with monitor_stage(monitor, "gql_fetch"):
                search_ids = [collect['id'] for collect in search_stories]
                collection_var = {
                    "where": {
                        "id": {
                            "in": search_ids
                        }   
                    }
                }
                data, _ = await gql_query_optimized(MESH_GQL_ENDPOINT, gql_collection_search, collection_var)
        else:
            search_ids = [collect['id'] for collect in search_stories]
            collection_var = {
                "where": {
                    "id": {
                        "in": search_ids
                    }   
                }
            }
            data, _ = await gql_query_optimized(MESH_GQL_ENDPOINT, gql_collection_search, collection_var)

        collections = data['collections']

        # 過濾和排序
        if monitor:
            async with monitor_stage(monitor, "post_processing"):
                content_table = {}
                for collect in collections:
                    id = collect['id']
                    status = collect['status']
                    if status == 'publish':
                        content_table[id] = collect
                related_collections = ranking_result(search_ids, content_table)
        else:
            content_table = {}
            for collect in collections:
                id = collect['id']
                status = collect['status']
                if status == 'publish':
                    content_table[id] = collect
            related_collections = ranking_result(search_ids, content_table)

        # 設定快取
        if monitor:
            async with monitor_stage(monitor, "cache_set"):
                await set_cache(key, json.dumps(related_collections), ttl=config.SEARCH_COLLECTION_CACHE_TTL)
        else:
            await set_cache(key, json.dumps(related_collections), ttl=config.SEARCH_COLLECTION_CACHE_TTL)

    except Exception as e:
        print("Search related collections error:", e)
        
    return related_collections

async def search_related_members_optimized(
    search_text: str, 
    num: int = config.MEILISEARCH_RELATED_MEMBER_NUM,
    monitor: Optional[PerformanceMonitor] = None
) -> List[Dict[str, Any]]:
    '''
    優化的成員搜尋函數
    '''
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    related_members = []
    
    try:
        # 檢查快取
        if monitor:
            async with monitor_stage(monitor, "cache_check"):
                prefix = FastAPICache.get_prefix()
                key = key_builder(f"{prefix}:search_members", search_text)
                _, cached_data = await get_cache(key)
                if cached_data:
                    return json.loads(cached_data)
        else:
            prefix = FastAPICache.get_prefix()
            key = key_builder(f"{prefix}:search_members", search_text)
            _, cached_data = await get_cache(key)
            if cached_data:
                return json.loads(cached_data)

        # MeiliSearch 搜尋
        if monitor:
            async with monitor_stage(monitor, "meilisearch_search"):
                client = get_meilisearch_client()
                search_members = client.index(config.MEILISEARCH_MEMBER_INDEX).search(search_text, {
                    'limit': num
                })['hits']
        else:
            client = get_meilisearch_client()
            search_members = client.index(config.MEILISEARCH_MEMBER_INDEX).search(search_text, {
                'limit': num
            })['hits']

        # 取得完整資訊
        if monitor:
            async with monitor_stage(monitor, "gql_fetch"):
                search_ids = [member['id'] for member in search_members]
                member_var = {
                    "where": {
                        "id": {
                            "in": search_ids
                        },
                        "is_active": {
                            "equals": True
                        }
                    }
                }
                data, _ = await gql_query_optimized(MESH_GQL_ENDPOINT, gql_member_search, member_var)
        else:
            search_ids = [member['id'] for member in search_members]
            member_var = {
                "where": {
                    "id": {
                        "in": search_ids
                    },
                    "is_active": {
                        "equals": True
                    }
                }
            }
            data, _ = await gql_query_optimized(MESH_GQL_ENDPOINT, gql_member_search, member_var)

        members = data['members']
        content_table = {member['id']: member for member in members}
        related_members = ranking_result(search_ids, content_table)

        # 設定快取
        if monitor:
            async with monitor_stage(monitor, "cache_set"):
                await set_cache(key, json.dumps(related_members), ttl=config.SEARCH_MEMBER_CACHE_TTL)
        else:
            await set_cache(key, json.dumps(related_members), ttl=config.SEARCH_MEMBER_CACHE_TTL)

    except Exception as e:
        print("Search related members error:", e)
        
    return related_members

async def search_related_publishers_optimized(
    search_text: str, 
    num: int = config.MEILISEARCH_RELATED_PUBLISHERS_NUM,
    monitor: Optional[PerformanceMonitor] = None
) -> List[Dict[str, Any]]:
    '''
    優化的發布者搜尋函數
    '''
    related_publishers = []
    
    try:
        # 檢查快取
        if monitor:
            async with monitor_stage(monitor, "cache_check"):
                prefix = FastAPICache.get_prefix()
                key = key_builder(f"{prefix}:search_publishers", search_text)
                _, cached_data = await get_cache(key)
                if cached_data:
                    return json.loads(cached_data)
        else:
            prefix = FastAPICache.get_prefix()
            key = key_builder(f"{prefix}:search_publishers", search_text)
            _, cached_data = await get_cache(key)
            if cached_data:
                return json.loads(cached_data)

        # MeiliSearch 搜尋
        if monitor:
            async with monitor_stage(monitor, "meilisearch_search"):
                client = get_meilisearch_client()
                related_publishers = client.index(config.MEILISEARCH_PUBLISHER_INDEX).search(search_text, {
                    'limit': num
                })['hits']
        else:
            client = get_meilisearch_client()
            related_publishers = client.index(config.MEILISEARCH_PUBLISHER_INDEX).search(search_text, {
                'limit': num
            })['hits']

        # 設定快取
        if monitor:
            async with monitor_stage(monitor, "cache_set"):
                await set_cache(key, json.dumps(related_publishers), ttl=config.SEARCH_PUBLISHER_CACHE_TTL)
        else:
            await set_cache(key, json.dumps(related_publishers), ttl=config.SEARCH_PUBLISHER_CACHE_TTL)

    except Exception as e:
        print("Search related publishers error:", e)
        
    return related_publishers

async def search_all_optimized(
    search_text: str, 
    objectives: List[str],
    monitor: Optional[PerformanceMonitor] = None
) -> Dict[str, List[Dict[str, Any]]]:
    '''
    並行執行所有搜尋類型的優化函數
    '''
    related_data = {}
    tasks = []
    
    # 建立並行任務
    if "story" in objectives:
        tasks.append(("story", search_related_stories_optimized(search_text, monitor=monitor)))
    if "collection" in objectives:
        tasks.append(("collection", search_related_collections_optimized(search_text, monitor=monitor)))
    if "member" in objectives:
        tasks.append(("member", search_related_members_optimized(search_text, monitor=monitor)))
    if "publisher" in objectives:
        tasks.append(("publisher", search_related_publishers_optimized(search_text, monitor=monitor)))
    
    # 並行執行所有任務
    if monitor:
        async with monitor_stage(monitor, "parallel_search"):
            if tasks:
                results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
                for i, (key, _) in enumerate(tasks):
                    if isinstance(results[i], Exception):
                        print(f"Search {key} error:", results[i])
                        related_data[key] = []
                    else:
                        related_data[key] = results[i]
    else:
        if tasks:
            results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
            for i, (key, _) in enumerate(tasks):
                if isinstance(results[i], Exception):
                    print(f"Search {key} error:", results[i])
                    related_data[key] = []
                else:
                    related_data[key] = results[i]
    
    return related_data 