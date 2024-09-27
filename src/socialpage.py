import pymongo
import os
import src.config as config

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
    social_member_page = []
    try:
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

        # filter picks
        picks = []
        for info in followings_info:
            mid = info['_id'] # member id
            story_reads = info['story_reads']
            story_comments = info['story_comments']
            for read in story_reads:
                read['member'] = {
                    "id": mid,
                    "customId": info['customId'],
                    "name": info['name'],
                    "avatar": info['avatar']
                }
                picks.append(read)
            for comment in story_comments:
                # data of comment would have additional field "content"
                comment['member'] = {
                    "id": mid,
                    "customId": info['customId'],
                    "name": info['name'],
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
                    "member": pick.get('member', None)
                }
                if kind == 'comment':
                    data['content'] = pick['content']
                categorized_picks.append(data)
            readCount = len(story.get('reads', []))
            commentCount = len(story.get('comments', []))
            social_member_page.append({
                "id": id,
                "url": story['url'],
                "publisher_id": story['publisher_id'],
                "og_title": story['og_title'],
                "og_image": story['og_image'],
                "og_description": story['og_description'],
                "readCount": readCount,
                "commentCount": commentCount,
                "following_actions": categorized_picks
            })
    except Exception as e:
        print(f'Error occurred when get socialpage for member: {member_id}, reason: {str(e)}')
    return social_member_page