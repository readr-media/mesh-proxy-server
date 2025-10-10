import os
import src.config as config
import random
from src.gql_optimized import gql_query_optimized, gql_all_publishers
from src.tool import get_isoformat_time, key_builder
from datetime import datetime
from fastapi_cache import FastAPICache
from src.cache import get_cache, set_cache
import json
from src.mongo_client import get_mongo_manager
from src.error_handler import ErrorHandler
import asyncio

async def getSocialPage_optimized(member_id: str, index: int = 0, take: int = 0):
    """
    優化的社交頁面獲取函數，使用 MongoDB 連接池和非同步操作
    """
    # request diagnostics
    print(f"[py/socialpage] req member_id={member_id} index={index} take={take} env={os.environ.get('ENV')}")

    ### check cached data
    prefix = FastAPICache.get_prefix()
    cache_key = key_builder(f"{prefix}", f"socialpage:{member_id}")
    _, cached_data = await get_cache(cache_key)
    if cached_data:
        print(f"[py/socialpage] cache hit key={cache_key} size={len(cached_data)}")
        social_page = json.loads(cached_data)
    else:
        social_stories, social_members = [], []
        gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
        
        # 使用優化的 GQL 查詢
        ErrorHandler.log_operation("GQL publishers query", {"endpoint": gql_endpoint})
        publishers, error = await gql_query_optimized(gql_endpoint, gql_all_publishers)
        
        gql_result = ErrorHandler.handle_gql_error(publishers, error, "publishers query")
        
        publishers_table = {}
        if gql_result["status"] == "success":
            publishers_data = gql_result["data"]
            publishers_list = ErrorHandler.safe_get(publishers_data, 'publishers', [])
            publishers_list = ErrorHandler.safe_list_operation(publishers_list, "publishers list")
            
            publishers_table = {
                publisher['id']: {
                    'title': publisher['title'],
                    'customId': publisher['customId'],
                } for publisher in publishers_list
                if isinstance(publisher, dict) and 'id' in publisher
            }
            
            ErrorHandler.log_operation("GQL publishers processing", {"processed_count": len(publishers_table)})
            print(f"[py/socialpage] publishers mapped={len(publishers_table)}")
        else:
            print(f"GQL publishers query failed: {gql_result['error']}")
            # 如果 GQL 查詢失敗，使用空字典繼續執行
        
        # 使用 MongoDB 連接池
        mongo_manager = await get_mongo_manager()
        db = mongo_manager.get_async_db()
        col_members, col_stories = db.members, db.stories
        
        # get the information about target member
        member_info = await col_members.find_one({"_id": member_id})
        if not member_info:
            print(f"Member not found: {member_id}")
            return {
                "timestamp": int(asyncio.get_event_loop().time()),
                "stories": [],
                "members": []
            }
        
        followings = member_info.get('following', [])
        mid_type = type(member_info.get('_id', None)).__name__
        print(f"[py/socialpage] member found _id_type={mid_type} following_count={len(followings)}")
        for i, v in enumerate(followings[:3]):
            print(f"[py/socialpage] following[{i}]={v} ({type(v).__name__})")
        if not followings:
            # 如果沒有關注者，返回空的社交頁面
            return {
                "timestamp": int(asyncio.get_event_loop().time()),
                "stories": [],
                "members": []
            }
        
        # 使用非同步查詢獲取關注者資訊
        print(f"[py/socialpage] followings query $in size={len(followings)}")
        followings_info = await col_members.find({
            "_id": {
                "$in": followings
            }
        }).to_list(length=None)
        print(f"[py/socialpage] followings fetched={len(followings_info)}")
        for i, info in enumerate(followings_info[:3]):
            _id = info.get('_id')
            print(f"[py/socialpage] followingsInfo[{i}]._id={_id} ({type(_id).__name__}) name={info.get('name')} nickname={info.get('nickname')}")
        
        # recommend following
        recommended_ids = set()
        recommend_from_table = {} # we can know recommend from whom by using this table
        for info in followings_info:
            # skip member who is not active
            is_active = info.get('is_active', True)
            if is_active == False:
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
        
        # 使用非同步查詢獲取推薦成員
        recommended_members_info = await col_members.find(
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
        ).to_list(length=None)
        
        for info in recommended_members_info:
            recommend_id = info["_id"]
            # skip member who is not active
            is_active = info.get('is_active', True)
            if is_active == False:
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
            if is_active == False:
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
        print(f"[py/socialpage] picks total={len(picks)}")
        
        # sort by timestamp
        sorted_picks = sorted(picks, key=lambda item: item['ts'], reverse=True)[:config.SOCIALPAGE_PICK_MAXNUM]
        story_ids = list(set([pick['sid'] for pick in sorted_picks]))
        print(f"[py/socialpage] storyIDs unique={len(story_ids)}")
        
        # make picks table for further reference
        picks_table = {}
        for pick in sorted_picks:
            data = picks_table.setdefault(pick['sid'], [])
            data.append(pick)

        # get full story content and organized all the informations
        story_list = await col_stories.find({"_id": {"$in": story_ids}}).to_list(length=None)
        print(f"[py/socialpage] stories fetched={len(story_list)}")
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
        social_page = {
            "timestamp": int(datetime.now().timestamp()),
            "stories": social_stories,
            "members": social_members
        }
        print(f"[py/socialpage] response stories={len(social_stories)} members={len(social_members)}")
        await set_cache(cache_key, json.dumps(social_page), config.SOCIALPAGE_CACHE_TIME)
    
    # support pagination
    if (index >= 0) and (take > 0):
        social_page['stories'] = social_page['stories'][index: index+take]
    return social_page 