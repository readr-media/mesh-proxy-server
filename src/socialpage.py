import pymongo
import os
import src.config as config
import random
from src.gql import gql_query, gql_all_publishers
from src.tool import get_isoformat_time, key_builder
from datetime import datetime
from fastapi_cache import FastAPICache
from src.cache import get_cache, set_cache
import json

def connect_db(mongo_url: str, env: str='dev'):
    client = pymongo.MongoClient(mongo_url)
    db = None
    if env=='staging':
        db = client.staging
    elif env=='prod':
        db = client.prod
    else:
        db = client.dev
    return db

async def getSocialPage(mongo_url: str, member_id: str, index: int=0, take: int=0):
    ### check cached data
    prefix = FastAPICache.get_prefix()
    cache_key = key_builder(f"{prefix}", f"socialpage:{member_id}")
    _, cached_data = await get_cache(cache_key)
    if cached_data:
        social_page = json.loads(cached_data)
    else:
        social_stories, social_members = [], []
        gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
        publishers, _ = gql_query(gql_endpoint, gql_all_publishers)
        publishers = publishers['publishers']
        publishers_table = {
            publisher['id']: {
                'title': publisher['title'],
                'customId': publisher['customId'],
            } for publisher in publishers
        }
        
        # connect to db
        db = connect_db(mongo_url, os.environ.get('ENV', 'dev'))
        col_members, col_stories = db.members, db.stories
        
        # get the information about target member
        member_info = col_members.find_one(member_id)
        followings = member_info['following']
        followings_info = list(
            col_members.find({
                "_id": {
                    "$in": followings
                }
            })
        )
        
        # recommend following
        recommended_ids = set()
        recommend_from_table = {} # we can know recommend from whom by using this table
        for info in followings_info:
            following_following = info['following']
            recommended_ids = recommended_ids.union(set(following_following))
            for id in following_following:
                recommend_from_list = recommend_from_table.setdefault(id, [])
                recommend_from_list.append({
                    'id': info['_id'],
                    'name': info['name'],
                    'nickname': info['nickname']
                })
        recommended_ids = list(recommended_ids.difference(set(followings)))
        random.shuffle(recommended_ids)
        recommended_members_info = list(col_members.find(
            {
                "_id": {
                    "$in": recommended_ids[:config.SOCIALPAGE_RECOMMEND_MEMBERS_NUM]
                }
            },
            {
                "story_reads": 0,
                "story_comments": 0,
                "following": 0,
            }
        ))
        for info in recommended_members_info:
            recommend_id = info["_id"]
            # skip member who is not active
            is_active = info.get('is_active', True)
            if is_active==False:
                continue
            recommend_from_candidates = recommend_from_table[recommend_id]
            social_members.append({
                "id": recommend_id,
                "followerCount": len(info.get('follower', [])),
                "name": info['name'],
                "nickname": info['nickname'],
                "customId": info['customId'],
                "avatar": info['avatar'],
                "from": random.choice(recommend_from_candidates)
            })

        # filter picks
        picks = []
        for info in followings_info:
            # skip member who is not active
            is_active = info.get('is_active', True)
            if is_active==False:
                continue
            mid = info['_id'] # member id
            story_reads = info['story_reads']
            story_comments = info['story_comments']
            for read in story_reads:
                read['member'] = {
                    "id": mid,
                    "name": info['name'],
                    "nickname": info['nickname'],
                    "customId": info['customId'],
                    "avatar": info['avatar']
                }
                picks.append(read)
            for comment in story_comments:
                # data of comment would have additional field "content"
                comment['member'] = {
                    "id": mid,
                    "name": info['name'],
                    "nickname": info['nickname'],
                    "customId": info['customId'],
                    "avatar": info['avatar']
                }
                picks.append(comment)
        
        # sort by timestamp
        sorted_picks = sorted(picks, key=lambda item: item['ts'], reverse=True)[:config.SOCIALPAGE_PICK_MAXNUM]
        story_ids = list(set([pick['sid'] for pick in sorted_picks]))
        
        # make picks table for further reference
        picks_table = {}
        for pick in sorted_picks:
            data = picks_table.setdefault(pick['sid'], [])
            data.append(pick)

        # get full story content and organized all the informations
        story_list = list(col_stories.find({"_id": {"$in": story_ids}}))
        full_story_info = {}
        for story in story_list:
            id = story['_id']
            publisher_id = story.get('publisher_id', None)
            # If the story is removed, don't show it
            if publisher_id == None:
                continue
            # If we can't find the corresponding picks for the story, don't show it
            table_pick = picks_table.get(id, None)
            if table_pick == None:
                continue
            categorized_picks = []
            for pick in table_pick:
                kind = 'comment' if pick.get('content', None) else 'read'
                data = {
                    "kind": kind,
                    "member": pick.get('member', None),
                    "createdAt": get_isoformat_time(pick['ts'])
                }
                if kind == 'comment':
                    data['content'] = pick['content']
                categorized_picks.append(data)
            readCount = len(story.get('reads', []))
            commentCount = len(story.get('comments', []))
            full_story_info[id] = {
                "id": id,
                "url": story['url'],
                "publisher": {
                    'id': publisher_id,
                    'title': publishers_table.get(publisher_id, {}).get('title', ''),
                    'customId': publishers_table.get(publisher_id, {}).get('customId', ''),
                },
                "og_title": story['og_title'],
                "og_image": story['og_image'],
                "og_description": story['og_description'],
                "full_screen_ad": story['full_screen_ad'],
                "isMember": story['isMember'],
                "published_date": story['published_date'],
                "readCount": readCount,
                "commentCount": commentCount,
                "following_actions": categorized_picks
            }
            
        # sort story by pick timestamp
        check_set = set()
        for pick in sorted_picks:
            sid = pick['sid']
            if sid in check_set:
                continue
            check_set.add(sid)
            story = full_story_info.get(sid, None)
            if story:
                social_stories.append(story)
        social_page = {
            "timestamp": int(datetime.now().timestamp()),
            "stories": social_stories,
            "members": social_members
        }
        await set_cache(cache_key, json.dumps(social_page), config.SOCIALPAGE_CACHE_TIME)
    # support pagination
    if (index>=0) and (take>0):
        social_page['stories'] = social_page['stories'][index: index+take]
    return social_page