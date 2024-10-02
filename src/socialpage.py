import pymongo
import os
import src.config as config
import random
from src.gql import gql_query, gql_all_publishers
from src.tool import get_isoformat_time

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

def getSocialPage(mongo_url: str, member_id: str):
    social_stories = []
    social_members = []
    try:
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
        for info in followings_info:
            recommended_ids = recommended_ids.union(set(info['following']))
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
            social_members.append({
                "id": info["_id"],
                "followerCount": len(info.get('follower', [])),
                "name": info['name'],
                "nickname": info['nickname'],
                "customId": info['customId'],
                "avatar": info['avatar']
            })

        # filter picks
        picks = []
        for info in followings_info:
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
        for story in story_list:
            id = story['_id']
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
            publisher_id = story['publisher_id']
            social_stories.append({
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
            })
    except Exception as e:
        print(f'Error occurred when get socialpage for member: {member_id}, reason: {str(e)}')
    social_page = {
        "stories": social_stories,
        "members": social_members
    }
    return social_page