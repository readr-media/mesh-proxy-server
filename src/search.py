import meilisearch
import os
import src.config as config
from src.gql import gql_query

gql_story_search = '''
query Stories($where: StoryWhereInput!){
  stories(where: $where, take: 5){
    id
    title
    og_title
    og_image
    og_description
    url
    isMember
    source{
      id
      customId
      is_active
    }
  }
}
'''

def search_related_stories(search_text: str, num: int=config.MEILISEARCH_RELATED_STORIES_NUM):
    MEILISEARCH_HOST = os.environ['MEILISEARCH_HOST']
    MEILISEARCH_APIKEY = os.environ['MEILISEARCH_APIKEY']
    related_stories = []
    try:
        client = meilisearch.Client(MEILISEARCH_HOST, MEILISEARCH_APIKEY)
        related_stories = client.index(config.MEILISEARCH_INDEX).search(search_text, {
            'showRankingScore': True, # If you want to show relavant score, show this
            'limit': num
        })['hits']
    except Exception as e:
        print("Search related stories error:", e)
    return related_stories

def search_related_stories_gql(search_text: str, num: int=config.MEILISEARCH_RELATED_STORIES_NUM):
    '''
    Given search text, return related stories. Full story content will be retrieved from CMS.
    '''
    MEILISEARCH_HOST = os.environ['MEILISEARCH_HOST']
    MEILISEARCH_APIKEY = os.environ['MEILISEARCH_APIKEY']
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    related_stories = []
    try:
        # search stories by content similarity
        client = meilisearch.Client(MEILISEARCH_HOST, MEILISEARCH_APIKEY)
        search_stories = client.index('mesh').search(search_text, {
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
        for story in stories:
            source = story.get('source', None)
            if source==None or isinstance(source, dict)==False:
                continue
            source_is_active = source.get('is_active', False)
            if source_is_active==False:
                continue
            related_stories.append(story)
    except Exception as e:
        print("Search related stories error:", e)
    return related_stories
    