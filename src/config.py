MAX_GQL_TTL=3600
MIN_GQL_TTL=5
DEFAULT_GQL_TTL=10
DEFAULT_LIST_AMOUNT=10000
DEFAULT_LATEST_STORIES_TTL = 3600
EXPIRE_LATEST_STORIES_TIME = 600
DEFAULT_LATEST_STORIES_TAKE = 10
DEFAULT_LATEST_STORIES_INDEX = 0

VERIFY_FAILED_ID = -2

MEILISEARCH_INDEX = 'mesh'
MEILISEARCH_RELATED_STORIES_NUM = 5
SEARCH_EXPIRE_TIME = 600
JWT_EXPIRE_HOURS = 3

### Support multiple different pubsub topics, key is the topic abbreviated name, value is the actions in the topic
PUBSUB_TOPIC_ACTIONS = {
    'payment': set([
        'unlock_story_single', 'unlock_story_media', 'unlock_all', 'deposit', 'sponsor_media'
    ])
}

PROXY_TIMEOUT_SEC = 30