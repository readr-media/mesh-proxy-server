import src.config as config
import os
import copy
from typing import Dict, List, Any
from src.mongo_client import get_mongo_manager
from src.notification_cache import get_notification_cache
from src.member_cache import get_member_cache
from src.performance_monitor import monitor_stage

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

async def get_notifies_optimized(mongo_url: str, memberId: str, index: int = 0, take: int = 10):
    """優化的通知取得函數"""
    from src.performance_monitor import get_current_monitor
    monitor = get_current_monitor()
    
    # 嘗試從快取取得
    notification_cache = get_notification_cache()
    cached_result = await notification_cache.get_cached_notifications(memberId, index, take)
    if cached_result is not None:
        if monitor:
            monitor.add_stage("notification_cache_hit", 0.001)
        return cached_result
    
    # 監控 MongoDB 查詢階段
    if monitor:
        async with monitor_stage(monitor, "mongo_query"):
            # 使用連接池
            mongo_manager = get_mongo_manager()
            db = mongo_manager.get_sync_db(mongo_url, os.environ.get('ENV', 'dev'))
            col_notify = db.notifications
            record = col_notify.find_one(memberId)
    
    empty_template = copy.deepcopy(empty_notifies)
    empty_template["id"] = memberId
    
    if record is None:
        if monitor:
            async with monitor_stage(monitor, "mongo_insert"):
                empty_mongo_template = copy.deepcopy(empty_mongo_notifies)
                empty_mongo_template["_id"] = memberId
                col_notify.insert_one(empty_mongo_template)
        
        # 快取空結果
        await notification_cache.set_cached_notifications(memberId, index, take, empty_template)
        return empty_template
    
    response = empty_template
    
    try:
        lrt = record.get('lrt', 0)
        all_notifies = record.get('notifies', [])
        all_notifies = all_notifies[index: index + take]
        
        # 監控通知處理階段
        if monitor:
            async with monitor_stage(monitor, "notification_processing"):
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
        
        # 監控成員資訊查詢階段
        if monitor:
            async with monitor_stage(monitor, "member_info_query"):
                member_cache = get_member_cache()
                member_table = await member_cache.get_members_info(notifiersId)
        
        # 監控完整通知生成階段
        if monitor:
            async with monitor_stage(monitor, "full_notification_generation"):
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
        
        # 快取結果
        await notification_cache.set_cached_notifications(memberId, index, take, response)
        
    except Exception as e:
        print("get_notifies_optimized error: ", e)
    
    return response 