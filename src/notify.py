import src.config as config
from src.gql import gql_query
import os
import copy

empty_mongo_notifies = {
    "_id": None,
    "lrt": 0,
    "notifies": [],
}

empty_notifies = {
    "id": None,
    "lrt": 0,
    "notifies": [],
}

gql_member_notifiers = '''
query Members($where: MemberWhereInput!){
  members(where: $where){
    id
    customId
    name
    avatar
  }
}
'''

def get_notifies(db, memberId: str, index: int=0, take: int=10):
    MESH_GQL_ENDPOINT = os.environ.get('MESH_GQL_ENDPOINT')
    
    if not MESH_GQL_ENDPOINT:
        print(f"❌ 錯誤: MESH_GQL_ENDPOINT 環境變數未設置")
        print(f"   請設置環境變數: export MESH_GQL_ENDPOINT=<your_gql_endpoint>")
        # 返回空的通知列表而不是崩潰
        empty_template = copy.deepcopy(empty_notifies)
        empty_template["id"] = memberId
        return empty_template
    
    print(f"🔍 檢查 MongoDB 連接:")
    try:
        col_notify = db.notifications
        
        # 測試連接
        db.command('ping')
        print(f"   ✅ MongoDB 連接正常")
        
        record = col_notify.find_one(memberId)
        
    except Exception as e:
        print(f"   ❌ MongoDB 連接失敗: {e}")
        # 返回空的通知列表
        empty_template = copy.deepcopy(empty_notifies)
        empty_template["id"] = memberId
        return empty_template
    
    empty_template = copy.deepcopy(empty_notifies)
    empty_template["id"] = memberId
    if record is None:
        empty_mongo_template = copy.deepcopy(empty_mongo_notifies)
        empty_mongo_template["_id"] = memberId
        col_notify.insert_one(empty_mongo_template)
        return empty_template     
    
    response = empty_template
    try:
        lrt = record.get('lrt', 0)
        all_notifies = record.get('notifies', [])
        all_notifies = all_notifies[index: index+take]

        # collect from_members information
        notifiersId = []
        targetObjs = {}
        for notify in all_notifies:
            action = notify['action']
            if action in config.PAYMENT_NOTIFIES:
              continue
            aggregate = notify['aggregate']
            membersId = notify['from']
            if aggregate==False:
                notifiersId.append(membersId)
            else:
                notifiersId.extend(membersId[:config.MAX_AVATAR_DISPLAYED])
            objective = notify['objective']
            targetId = notify['targetId']
            targetId_list = targetObjs.setdefault(objective, [])
            targetId_list.append(targetId)
        notifiersId = list(set(notifiersId))

        # search member's full information
        mutation = {
            "where": {
                "id": {
                    "in": notifiersId
                }
            }
        }
        members, _ = gql_query(MESH_GQL_ENDPOINT, gql_member_notifiers, mutation)
        members = members['members']
        member_table = {}
        for member in members:
            id = member['id']
            member_table[id] = member

        # generate the full notifies information
        full_notifies = []
        for notify in all_notifies:
            action = notify['action']
            if action in config.PAYMENT_NOTIFIES:
              full_notifies.append(notify)
              continue
            aggregate = notify["aggregate"]
            from_notifiers = notify["from"]
            objective = notify['objective']
            targetId = notify['targetId']
            len_notifiers = len(from_notifiers) if aggregate==True else 1
            
            notifiers = []
            if aggregate==True:
                notifiersId = from_notifiers[:config.MAX_AVATAR_DISPLAYED]
                for notifierId in notifiersId:
                    notifier = member_table.get(notifierId, None)
                    if notifier:
                        notifiers.append(notifier)
            else:
                notifier = member_table.get(from_notifiers, None)
                if notifier:
                    notifiers.append(notifier)
                else:
                    print(f"cannot get memberId: {from_notifiers}")
                    print(f"   成員表大小: {len(member_table)}")
                    print(f"   可用的成員 ID: {list(member_table.keys())}")
            full_notify = {
                "uuid": notify["uuid"],
                "read": notify["read"],
                "action": notify["action"],
                "objective": objective,
                "targetId": targetId,
                "aggregate": aggregate,
                "notifiers_num": len_notifiers,
                "notifiers": notifiers,
                "ts": notify["ts"]
            }
            
            # content is optional field, which is used as appendix
            content = notify.get('content', None)
            if content:
                full_notify['content'] = content
            full_notifies.append(full_notify)
        response = {
            "id": memberId,
            "lrt": lrt,
            "notifies": full_notifies
        }
    except Exception as e:
        print("get_notifies error: ", e)
    return response