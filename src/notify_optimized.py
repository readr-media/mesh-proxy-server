import src.config as config
from src.gql_optimized import gql_query_optimized
import os
import copy
from src.mongo_client import get_mongo_manager
from src.error_handler import ErrorHandler

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
    MESH_GQL_ENDPOINT = os.environ.get('MESH_GQL_ENDPOINT')
    
    if not MESH_GQL_ENDPOINT:
        print(f"❌ 錯誤: MESH_GQL_ENDPOINT 環境變數未設置")
        print(f"   請設置環境變數: export MESH_GQL_ENDPOINT=<your_gql_endpoint>")
        # 返回空的通知列表而不是崩潰
        empty_template = copy.deepcopy(empty_notifies)
        empty_template["id"] = memberId
        return empty_template
    
    # 使用 MongoDB 連接池
    mongo_manager = await get_mongo_manager()
    db = mongo_manager.get_async_db()
    col_notify = db.notifications
    
    # 使用非同步查詢
    record = await col_notify.find_one({"_id": memberId})
    
    # 如果找不到記錄，創建一個空的記錄
    if record is None:
        empty_mongo_template = copy.deepcopy(empty_mongo_notifies)
        empty_mongo_template["_id"] = memberId
        try:
            await col_notify.insert_one(empty_mongo_template)
        except Exception as e:
            print(f"Failed to insert empty notification record: {e}")
        return empty_template
    
    empty_template = copy.deepcopy(empty_notifies)
    empty_template["id"] = memberId
    
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
        if notifiersId:  # 只有在有通知者 ID 時才查詢
            mutation = {
                "where": {
                    "id": {
                        "in": notifiersId
                    }
                }
            }
            
            print(f"🔍 查詢成員信息: {notifiersId}")
            print(f"   GQL 端點: {MESH_GQL_ENDPOINT}")
            print(f"   查詢變數: {mutation}")
            print(f"   GQL 查詢字符串: {gql_member_notifiers}")
            
            ErrorHandler.log_operation("GQL members query", {"notifiers_count": len(notifiersId)})
            members, error = await gql_query_optimized(MESH_GQL_ENDPOINT, gql_member_notifiers, mutation)
            
            # 添加詳細的響應調試
            if members:
                print(f"   GQL 響應結構: {list(members.keys())}")
                if 'errors' in members:
                    print(f"   ❌ GQL 錯誤: {members['errors']}")
                if 'data' in members:
                    data = members['data']
                    print(f"   數據字段: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    if 'members' in data:
                        members_list = data['members']
                        print(f"   成員列表類型: {type(members_list)}")
                        print(f"   成員列表長度: {len(members_list) if isinstance(members_list, list) else 'Not a list'}")
            else:
                print(f"   ❌ GQL 響應為 None")
            
            if error:
                print(f"❌ GQL 查詢錯誤: {error}")
                member_table = {}
            else:
                gql_result = ErrorHandler.handle_gql_error(members, error, "members query")
                
                member_table = {}
                if gql_result["status"] == "success":
                    members_data = gql_result["data"]
                    members_list = ErrorHandler.safe_get(members_data, 'members', [])
                    members_list = ErrorHandler.safe_list_operation(members_list, "members list")
                    
                    for member in members_list:
                        if isinstance(member, dict) and 'id' in member:
                            id = member['id']
                            member_table[id] = member
                    
                    print(f"✅ 成功獲取 {len(member_table)} 個成員信息")
                    ErrorHandler.log_operation("GQL members processing", {"processed_count": len(member_table)})
                else:
                    print(f"❌ GQL members query failed: {gql_result['error']}")
                    # 如果 GQL 查詢失敗，使用空字典繼續執行
        else:
            member_table = {}
            print("No notifiers to query")

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
                    print(f"cannot get memberId: {from_notifiers}")
                    # 添加調試信息
                    try:
                        from src.notify_debug import debug_notification_issue
                        debug_info = debug_notification_issue(
                            from_notifiers, 
                            member_table, 
                            {"action": action, "objective": objective, "targetId": targetId}
                        )
                        print(f"   調試信息: 成員表大小={debug_info['member_table_size']}, 相似ID={debug_info['similar_ids']}")
                    except Exception as debug_error:
                        print(f"   調試失敗: {debug_error}")
                    
                    # 創建模擬成員以避免錯誤
                    try:
                        from src.notify_debug import NotifyDebugger
                        mock_member = NotifyDebugger.create_mock_member(from_notifiers)
                        notifiers.append(mock_member)
                        print(f"   已創建模擬成員: {from_notifiers}")
                    except Exception as mock_error:
                        print(f"   創建模擬成員失敗: {mock_error}")
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
        print(f"❌ 處理通知時發生錯誤: {e}")
        # 返回空的通知列表
        response["lrt"] = 0
        response["notifies"] = []
    
    return response 