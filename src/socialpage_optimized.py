import src.config as config
from src.gql import gql_query
import os
import copy
import json
import random
from datetime import datetime
from typing import Dict, List, Any
from src.mongo_client import get_mongo_manager
from src.cache import get_cache, set_cache
from src.tool import key_builder
from fastapi_cache import FastAPICache
from src.performance_monitor import monitor_stage

gql_all_publishers = '''
query {
  publishers {
    id
    title
    customId
  }
}
'''

def get_isoformat_time(timestamp):
    """Convert timestamp to ISO format"""
    return datetime.fromtimestamp(timestamp).isoformat()

async def getSocialPage_optimized(mongo_url: str, member_id: str, index: int = 0, take: int = 0):
    """優化的社交頁面取得函數"""
    from src.performance_monitor import get_current_monitor
    monitor = get_current_monitor()
    
    ### check cached data
    prefix = FastAPICache.get_prefix()
    cache_key = key_builder(f"{prefix}", f"socialpage:{member_id}")
    _, cached_data = await get_cache(cache_key)
    
    if cached_data:
        if monitor:
            monitor.add_stage("socialpage_cache_hit", 0.001)
        social_page = json.loads(cached_data)
    else:
        social_stories, social_members = [], []
        
        # 監控 GQL 查詢階段
        if monitor:
            async with monitor_stage(monitor, "gql_publishers_query"):
                gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
                publishers, _ = gql_query(gql_endpoint, gql_all_publishers)
                publishers = publishers['publishers']
                publishers_table = {
                    publisher['id']: {
                        'title': publisher['title'],
                        'customId': publisher['customId'],
                    } for publisher in publishers
                }
        
        # 監控 MongoDB 查詢階段
        if monitor:
            async with monitor_stage(monitor, "mongo_members_query"):
                # 使用連接池
                mongo_manager = get_mongo_manager()
                db = mongo_manager.get_sync_db(mongo_url, os.environ.get('ENV', 'dev'))
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
        
        # 監控推薦邏輯處理階段
        if monitor:
            async with monitor_stage(monitor, "recommendation_processing"):
                # recommend following
                recommended_ids = set()
                recommend_from_table = {} # we can know recommend from whom by using this table
                for info in followings_info:
                    # skip member who is not active
                    is_active = info.get('is_active', True)
                    if is_active==False:
                        print(f"Socialpage: Member {info['name']} is not active.")
                        continue
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
        
        # 監控內容處理階段
        if monitor:
            async with monitor_stage(monitor, "content_processing"):
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
        
        # 監控故事查詢階段
        if monitor:
            async with monitor_stage(monitor, "mongo_stories_query"):
                # get full story content and organized all the informations
                story_list = list(col_stories.find({"_id": {"$in": story_ids}}))
        
        # 監控故事處理階段
        if monitor:
            async with monitor_stage(monitor, "story_processing"):
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
                        "story_type": story.get('story_type', 'story'),
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
        
        # 監控快取設定階段
        if monitor:
            async with monitor_stage(monitor, "cache_setting"):
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