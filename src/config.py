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
MEILISEARCH_MEMBER_INDEX = 'mesh_member'
MEILISEARCH_PUBLISHER_INDEX = 'mesh_publisher'
MEILISEARCH_RELATED_STORIES_NUM = 10
MEILISEARCH_RELATED_COLLECTIONS_NUM = 5
MEILISEARCH_RELATED_MEMBER_NUM = 10
MEILISEARCH_RELATED_PUBLISHERS_NUM = 3

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

DEFAULT_NOTIFY_TAKE_NUM = 10
NOTIFY_TAKE_NUM = os.environ.get('NOTIFY_TAKE_NUM', DEFAULT_NOTIFY_TAKE_NUM)

DEFAULT_NOTIFY_INDEX = 0
NOTIFY_INDEX = os.environ.get('NOTIFY_INDEX', DEFAULT_NOTIFY_INDEX)

DEFAULT_MAX_AVATAR_DISPLAYED = 2
MAX_AVATAR_DISPLAYED = os.environ.get('MAX_AVATAR_DISPLAYED', DEFAULT_MAX_AVATAR_DISPLAYED)

DEFAULT_SIGNED_COOKIE_TTL = 3600
SIGNED_COOKIE_TTL = os.environ.get('SIGNED_COOKIE_TTL', DEFAULT_SIGNED_COOKIE_TTL)

### Support multiple different pubsub topics, key is the topic abbreviated name, value is the actions in the topic
PUBSUB_TOPIC_ACTIONS = {
    'payment': set([
        'unlock_story_single', 'unlock_story_media', 'unlock_all', 'deposit', 'sponsor_media'
    ])
}

### For searching
VALID_SEARCH_OBJECTIVES = set([
    "story", "collection", "member", "publisher"
])

DEFAULT_SEARCH_STORY_CACHE_TTL = 3600
SEARCH_STORY_CACHE_TTL = os.environ.get('SEARCH_STORY_CACHE_TTL', DEFAULT_SEARCH_STORY_CACHE_TTL)

DEFAULT_SEARCH_COLLECTION_CACHE_TTL = 300
SEARCH_COLLECTION_CACHE_TTL = os.environ.get('SEARCH_COLLECTION_CACHE_TTL', DEFAULT_SEARCH_COLLECTION_CACHE_TTL)

DEFAULT_SEARCH_MEMBER_CACHE_TTL = 300
SEARCH_MEMBER_CACHE_TTL = os.environ.get('SEARCH_MEMBER_CACHE_TTL', DEFAULT_SEARCH_MEMBER_CACHE_TTL)

DEFAULT_SEARCH_PUBLISHER_CACHE_TTL = 3600
SEARCH_PUBLISHER_CACHE_TTL = os.environ.get('SEARCH_PUBLISHER_CACHE_TTL', DEFAULT_SEARCH_PUBLISHER_CACHE_TTL)

# maximum and default search result num
DEFAULT_SEARCH_NUM = 10
SEARCH_NUM = os.environ.get('SEARCH_NUM', DEFAULT_SEARCH_NUM)

DEAFAULT_MAX_SEARCH_NUM = 100
MAX_SEARCH_NUM = os.environ.get('MAX_SEARCH_NUM', DEAFAULT_MAX_SEARCH_NUM)

### For notification
PAYMENT_NOTIFIES = set(["notify_transaction", "notify_sponsorship", "approach_expiration"])

PROXY_TIMEOUT_SEC = 30