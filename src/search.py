import meilisearch
import os
import src.config as config

def search_related_stories(search_text: str, num: int=config.MEILISEARCH_RELATED_STORIES_NUM):
    MEILISEARCH_HOST = os.environ['MEILISEARCH_HOST']
    MEILISEARCH_APIKEY = os.environ['MEILISEARCH_APIKEY']
    related_stories = []
    try:
        client = meilisearch.Client(MEILISEARCH_HOST, MEILISEARCH_APIKEY)
        related_stories = client.index(config.MEILISEARCH_INDEX).search(search_text, {
            'showRankingScore': True,
            'limit': num
        })['hits']
    except Exception as e:
        print("Search related stories error:", e)
    return related_stories
    