import src.config as config
from src.gql_optimized import gql_query_optimized
import os
import copy
from src.mongo_client import get_mongo_manager

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

async def get_notifies_optimized(memberId: str, index: int = 0, take: int = 10):
    """
    優化的通知獲取函數，使用 MongoDB 連接池和非同步操作
    """
    MESH_GQL_ENDPOINT = os.environ['MESH_GQL_ENDPOINT']
    
    # 使用 MongoDB 連接池
    mongo_manager = await get_mongo_manager()
    db = mongo_manager.get_async_db()
    col_notify = db.notifications
    
    # 使用非同步查詢
    record = await col_notify.find_one({"_id": memberId})
    
    empty_template = copy.deepcopy(empty_notifies)
    empty_template["id"] = memberId
    
    if record is None:
        empty_mongo_template = copy.deepcopy(empty_mongo_notifies)
        empty_mongo_template["_id"] = memberId
        await col_notify.insert_one(empty_mongo_template)
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
            if aggregate == False:
                notifiersId.append(membersId)
            else:
                notifiersId.extend(membersId[:config.MAX_AVATAR_DISPLAYED])
            objective = notify['objective']
            targetId = notify['targetId']
            targetId_list = targetObjs.setdefault(objective, [])
            targetId_list.append(targetId)
        notifiersId = list(set(notifiersId))

        # search member's full information using optimized GQL
        mutation = {
            "where": {
                "id": {
                    "in": notifiersId
                }
            }
        }
        members, _ = await gql_query_optimized(MESH_GQL_ENDPOINT, gql_member_notifiers, mutation)
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
            len_notifiers = len(from_notifiers) if aggregate == True else 1
            
            notifiers = []
            if aggregate == True:
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
                    print(f"cannot get memberId: {memberId}")
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