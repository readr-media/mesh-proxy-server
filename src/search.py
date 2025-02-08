import meilisearch
import os
import src.config as config
from src.gql import gql_query

from fastapi_cache import FastAPICache
from src.cache import get_cache, set_cache
from src.tool import key_builder
import json

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

async def search_related_stories(client, search_text: str, num: int=config.MEILISEARCH_RELATED_STORIES_NUM):
    '''
    Given search text, return related stories. Full story content will be retrieved from CMS.
    '''
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    related_stories = []
    try:
        # check the cache in redis
        prefix = FastAPICache.get_prefix()
        key = key_builder(f"{prefix}:search_stories", search_text)
        _, cached_data = await get_cache(key)
        if cached_data:
            # cache hit
            related_stories = json.loads(cached_data)
        else:
            # search stories by content similarity
            search_stories = client.index(config.MEILISEARCH_STORY_INDEX).search(search_text, {
                'attributesToRetrieve': ['id', 'title'],
                'limit': num
            })['hits']

            # get full info from gql
            search_ids = [story['id'] for story in search_stories]
            search_var = {
                "where": {
                    "id": {
                        "in": search_ids
                    }
                }
            }
            stories, err = gql_query(MESH_GQL_ENDPOINT, gql_story_search, search_var)
            if err==None and isinstance(stories, dict)==True:
                stories = stories['stories']
            else:
                raise(str(err))

            # post-filtering the stories
            content_table = {}
            for story in stories:
                id = story.get('id', None)
                source = story.get('source', None)
                if id==None or source==None or isinstance(source, dict)==False:
                    continue
                source_is_active = source.get('is_active', False)
                if source_is_active==False:
                    continue
                content_table[id] = story
            
            # ranking related stories
            related_stories = ranking_result(search_ids, content_table)
            await set_cache(key, json.dumps(related_stories), ttl=config.SEARCH_STORY_CACHE_TTL)
    except Exception as e:
        print("Search related stories error:", e)
    return related_stories

def search_related_collections(client, search_text: str, num: int=config.MEILISEARCH_RELATED_COLLECTIONS_NUM):
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    related_collections = []
    try:
        # search collections by content similarity
        search_stories = client.index(config.MEILISEARCH_COLLECTION_INDEX).search(search_text, {
            'limit': num
        })['hits']

        # search full information in cms
        search_ids = [collect['id'] for collect in search_stories]
        collection_var = {
            "where": {
                "id": {
                    "in": search_ids
                }   
            }
        }
        data, _ = gql_query(MESH_GQL_ENDPOINT, gql_collection_search, collection_var)
        collections = data['collections']

        # filter out status not publish
        content_table = {}
        for collect in collections:
            id = collect['id']
            status = collect['status']
            if status=='publish':
                content_table[id] = collect
        related_collections = ranking_result(search_ids, content_table)
    except Exception as e:
        print("Search related collections error:", e)
    return related_collections
  
def search_related_members(client, search_text: str, num: int=config.MEILISEARCH_RELATED_MEMBER_NUM):
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    related_members = []
    try:
        # search members by content similarity
        search_members = client.index(config.MEILISEARCH_MEMBER_INDEX).search(search_text, {
            'limit': num
        })['hits']

        # search full information in cms
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
        data, _ = gql_query(MESH_GQL_ENDPOINT, gql_member_search, member_var)
        members = data['members']
        content_table = {member['id']: member for member in members}
        related_members = ranking_result(search_ids, content_table)
    except Exception as e:
        print("Search related members error:", e)
    return related_members

def search_related_publishers(client, search_text: str, num: int=config.MEILISEARCH_RELATED_PUBLISHERS_NUM):
    related_publishers = []
    try:
        # search stories by content similarity
        related_publishers = client.index(config.MEILISEARCH_PUBLISHER_INDEX).search(search_text, {
            'limit': num
        })['hits']
    except Exception as e:
        print("Search related publishers error:", e)
    return related_publishers