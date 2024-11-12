import os

MAX_GQL_TTL=3600
MIN_GQL_TTL=5
DEFAULT_GQL_EXEC_TIMEOUT = 30
DEFAULT_GQL_TTL=10
DEFAULT_LIST_AMOUNT=10000
DEFAULT_LATEST_STORIES_TTL = 3600
EXPIRE_LATEST_STORIES_TIME = 600
DEFAULT_LATEST_STORIES_TAKE = 10
DEFAULT_LATEST_STORIES_INDEX = 0

VERIFY_FAILED_ID = -2

MEILISEARCH_STORY_INDEX = 'mesh'
MEILISEARCH_COLLECTION_INDEX = 'mesh_collection'
MEILISEARCH_RELATED_STORIES_NUM = 10
MEILISEARCH_RELATED_COLLECTIONS_NUM = 5

DEFAULT_SEARCH_EXPIRE_TIME = 600
SEARCH_EXPIRE_TIME = os.environ.get('SEARCH_EXPIRE_TIME', DEFAULT_SEARCH_EXPIRE_TIME)

DEFAULT_JWT_EXPIRE_HOURS = 12
JWT_EXPIRE_HOURS = os.environ.get('JWT_EXPIRE_HOURS', DEFAULT_JWT_EXPIRE_HOURS)

DEFAULT_SOCIALPAGE_PICK_MAXNUM = 1000
SOCIALPAGE_PICK_MAXNUM = os.environ.get('SOCIALPAGE_PICK_MAXNUM', DEFAULT_SOCIALPAGE_PICK_MAXNUM)

DEFAULT_SOCIALPAGE_CACHE_TIME = 300
SOCIALPAGE_CACHE_TIME = os.environ.get('SOCIALPAGE_CACHE_TIME', DEFAULT_SOCIALPAGE_CACHE_TIME)

DEFAULT_SOCIALPAGE_RECOMMEND_MEMBERS_NUM = 20
SOCIALPAGE_RECOMMEND_MEMBERS_NUM = os.environ.get('SOCIALPAGE_RECOMMEND_MEMBERS_NUM', DEFAULT_SOCIALPAGE_RECOMMEND_MEMBERS_NUM)

DEFAULT_INVITATION_CODE_CHARS = 6
INVITATION_CODE_CHARS = os.environ.get('INVITATION_CODE_CHARS', DEFAULT_INVITATION_CODE_CHARS)

DEFAULT_INVITATION_CODE_NUMS = 5
INVITATION_CODE_NUMS = os.environ.get('INVITATION_CODE_NUMS', DEFAULT_INVITATION_CODE_NUMS)

### Support multiple different pubsub topics, key is the topic abbreviated name, value is the actions in the topic
PUBSUB_TOPIC_ACTIONS = {
    'payment': set([
        'unlock_story_single', 'unlock_story_media', 'unlock_all', 'deposit', 'sponsor_media'
    ])
}

### For searching
VALID_SEARCH_OBJECTIVES = set([
    "story", "collection", "member"
])

PROXY_TIMEOUT_SEC = 30