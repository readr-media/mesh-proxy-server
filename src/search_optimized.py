import src.config as config
import os
import json
import meilisearch
from fastapi_cache import FastAPICache
from src.tool import key_builder
from src.cache import get_cache, set_cache
from src.member_cache import get_member_cache
from src.performance_monitor import monitor_stage

gql_story_search = '''
query Stories($where: StoryWhereInput!){
    stories(where: $where){
        id
        title
        source{
            id
            title
            is_active
        }
        url
        summary
        content
        og_title
        og_image
        og_description
        full_screen_ad
        isMember
        published_date
        story_type
        reads{
            id
        }
        comments{
            id
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
        description
        image
        stories{
            id
            title
            url
            og_image
        }
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

def connect_meilisearch():
    MEILISEARCH_HOST = os.environ['MEILISEARCH_HOST']
    MEILISEARCH_APIKEY = os.environ['MEILISEARCH_APIKEY']
    client = meilisearch.Client(MEILISEARCH_HOST, MEILISEARCH_APIKEY)
    return client

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

async def search_related_stories(client, search_text: str, num: int = config.MEILISEARCH_RELATED_STORIES_NUM):
    '''
    Given search text, return related stories. Full story content will be retrieved from CMS.
    '''
    from src.performance_monitor import get_current_monitor
    monitor = get_current_monitor()
    
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    related_stories = []
    
    try:
        # check the cache in redis
        prefix = FastAPICache.get_prefix()
        key = key_builder(f"{prefix}:search_stories", search_text)
        _, cached_data = await get_cache(key)
        
        if cached_data:
            if monitor:
                monitor.add_stage("story_search_cache_hit", 0.001)
            # cache hit
            related_stories = json.loads(cached_data)
        else:
            # 監控 Meilisearch 查詢階段
            if monitor:
                async with monitor_stage(monitor, "meilisearch_story_query"):
                    # search stories by content similarity
                    search_stories = client.index(config.MEILISEARCH_STORY_INDEX).search(search_text, {
                        'attributesToRetrieve': ['id', 'title'],
                        'limit': num
                    })['hits']
            
            # 監控 GQL 查詢階段
            if monitor:
                async with monitor_stage(monitor, "gql_story_query"):
                    # get full info from gql
                    search_ids = [story['id'] for story in search_stories]
                    search_var = {
                        "where": {
                            "id": {
                                "in": search_ids
                            }
                        }
                    }
                    from src.http_client import get_http_client
                    http_client = await get_http_client()
                    stories, err = await http_client.post_json(MESH_GQL_ENDPOINT, {"query": gql_story_search, "variables": search_var}, {})
                    
                    if err == None and isinstance(stories, dict) == True:
                        stories = stories['data']['stories']
                    else:
                        raise Exception(str(err))
            
            # 監控故事處理階段
            if monitor:
                async with monitor_stage(monitor, "story_processing"):
                    # post-filtering the stories
                    content_table = {}
                    for story in stories:
                        id = story.get('id', None)
                        source = story.get('source', None)
                        if id == None or source == None or isinstance(source, dict) == False:
                            continue
                        source_is_active = source.get('is_active', False)
                        if source_is_active == False:
                            continue
                        content_table[id] = story
                    
                    # ranking related stories
                    related_stories = ranking_result(search_ids, content_table)
            
            # 監控快取設定階段
            if monitor:
                async with monitor_stage(monitor, "story_cache_setting"):
                    await set_cache(key, json.dumps(related_stories), ttl=config.SEARCH_STORY_CACHE_TTL)
                    
    except Exception as e:
        print("Search related stories error:", e)
    return related_stories

async def search_related_collections(client, search_text: str, num: int = config.MEILISEARCH_RELATED_COLLECTIONS_NUM):
    from src.performance_monitor import get_current_monitor
    monitor = get_current_monitor()
    
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    related_collections = []
    
    try:
        # 監控 Meilisearch 查詢階段
        if monitor:
            async with monitor_stage(monitor, "meilisearch_collection_query"):
                # search collections by content similarity
                search_stories = client.index(config.MEILISEARCH_COLLECTION_INDEX).search(search_text, {
                    'limit': num
                })['hits']
        
        # 監控 GQL 查詢階段
        if monitor:
            async with monitor_stage(monitor, "gql_collection_query"):
                # search full information in cms
                search_ids = [collect['id'] for collect in search_stories]
                collection_var = {
                    "where": {
                        "id": {
                            "in": search_ids
                        }   
                    }
                }
                from src.http_client import get_http_client
                http_client = await get_http_client()
                data, _ = await http_client.post_json(MESH_GQL_ENDPOINT, {"query": gql_collection_search, "variables": collection_var}, {})
                collections = data['data']['collections']
        
        # 監控集合處理階段
        if monitor:
            async with monitor_stage(monitor, "collection_processing"):
                # filter out status not publish
                content_table = {}
                for collect in collections:
                    id = collect['id']
                    status = collect['status']
                    if status == 'publish':
                        content_table[id] = collect
                related_collections = ranking_result(search_ids, content_table)
                
    except Exception as e:
        print("Search related collections error:", e)
    return related_collections

async def search_related_members(client, search_text: str, num: int = config.MEILISEARCH_RELATED_MEMBER_NUM):
    from src.performance_monitor import get_current_monitor
    monitor = get_current_monitor()
    
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    related_members = []
    
    try:
        # 監控 Meilisearch 查詢階段
        if monitor:
            async with monitor_stage(monitor, "meilisearch_member_query"):
                # search members by content similarity
                search_members = client.index(config.MEILISEARCH_MEMBER_INDEX).search(search_text, {
                    'limit': num
                })['hits']
        
        # 監控成員資訊查詢階段
        if monitor:
            async with monitor_stage(monitor, "member_info_query"):
                # search full information in cms
                search_ids = [member['id'] for member in search_members]
                
                # 使用 member_cache
                member_cache = get_member_cache()
                members_data = await member_cache.get_members_info(search_ids)
                
                # 過濾活躍成員
                content_table = {}
                for member_id, member in members_data.items():
                    if member.get('is_active', False):
                        content_table[member_id] = member
                
                related_members = ranking_result(search_ids, content_table)
                
    except Exception as e:
        print("Search related members error:", e)
    return related_members

async def search_related_publishers(client, search_text: str, num: int = config.MEILISEARCH_RELATED_PUBLISHERS_NUM):
    from src.performance_monitor import get_current_monitor
    monitor = get_current_monitor()
    
    related_publishers = []
    try:
        # 監控 Meilisearch 查詢階段
        if monitor:
            async with monitor_stage(monitor, "meilisearch_publisher_query"):
                # search stories by content similarity
                related_publishers = client.index(config.MEILISEARCH_PUBLISHER_INDEX).search(search_text, {
                    'limit': num
                })['hits']
                
    except Exception as e:
        print("Search related publishers error:", e)
    return related_publishers 