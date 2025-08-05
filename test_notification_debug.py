#!/usr/bin/env python3
"""
測試通知調試功能
"""

import asyncio
import os
from src.notify_debug import NotifyDebugger, analyze_notifications, debug_notification_issue

async def test_notification_debug():
    """測試通知調試功能"""
    print("🧪 測試通知調試功能...")
    
    # 模擬一些通知資料
    test_notifications = [
        {
            "uuid": "test1",
            "action": "follow",
            "from": "member_183",  # 這個 ID 可能不存在
            "aggregate": False,
            "objective": "member",
            "targetId": "member_456",
            "read": False,
            "ts": 1234567890
        },
        {
            "uuid": "test2",
            "action": "like",
            "from": ["member_123", "member_456", "member_789"],
            "aggregate": True,
            "objective": "story",
            "targetId": "story_123",
            "read": False,
            "ts": 1234567891
        },
        {
            "uuid": "test3",
            "action": "payment_success",
            "from": "member_999",
            "aggregate": False,
            "objective": "payment",
            "targetId": "payment_123",
            "read": False,
            "ts": 1234567892
        }
    ]
    
    # 模擬成員表
    member_table = {
        "member_123": {
            "id": "member_123",
            "name": "測試用戶1",
            "nickname": "測試1",
            "customId": "test1",
            "avatar": "https://example.com/avatar1.jpg"
        },
        "member_456": {
            "id": "member_456",
            "name": "測試用戶2",
            "nickname": "測試2",
            "customId": "test2",
            "avatar": "https://example.com/avatar2.jpg"
        }
    }
    
    print("\n1. 分析通知資料...")
    analysis = analyze_notifications(test_notifications)
    
    print("\n2. 測試成員查找調試...")
    debug_info = debug_notification_issue("member_183", member_table, {"action": "follow"})
    
    print("\n3. 測試模擬成員創建...")
    mock_member = NotifyDebugger.create_mock_member("member_183")
    print(f"   模擬成員: {mock_member}")
    
    print("\n4. 測試實際的通知處理...")
    try:
        from src.notify_optimized import get_notifies_optimized
        
        # 檢查環境變數
        if not os.environ.get('MONGO_URL'):
            print("   ⚠️ 未設定 MONGO_URL，跳過實際測試")
            return
        
        # 測試實際的通知獲取
        result = await get_notifies_optimized("test_member", 0, 10)
        print(f"   實際測試結果: {type(result)}")
        if result:
            print(f"   通知數量: {len(result.get('notifies', []))}")
        
    except Exception as e:
        print(f"   ❌ 實際測試失敗: {e}")
    
    print("\n🎉 通知調試測試完成！")

def test_member_id_analysis():
    """分析成員 ID 183 的問題"""
    print("\n🔍 分析成員 ID 183 的問題...")
    
    # 模擬不同的情況
    scenarios = [
        {
            "name": "成員 ID 存在",
            "member_id": "183",
            "member_table": {"183": {"id": "183", "name": "用戶183"}},
            "expected": "應該找到成員"
        },
        {
            "name": "成員 ID 不存在",
            "member_id": "183",
            "member_table": {"184": {"id": "184", "name": "用戶184"}},
            "expected": "應該找不到成員，創建模擬成員"
        },
        {
            "name": "成員 ID 格式不同",
            "member_id": "183",
            "member_table": {"member_183": {"id": "member_183", "name": "用戶member_183"}},
            "expected": "應該找不到成員，但可能有相似 ID"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n   測試場景: {scenario['name']}")
        print(f"   預期結果: {scenario['expected']}")
        
        debug_info = debug_notification_issue(
            scenario['member_id'], 
            scenario['member_table'], 
            {"action": "test"}
        )
        
        if debug_info['member_found']:
            print(f"   ✅ 找到成員: {debug_info['member_data']['name']}")
        else:
            print(f"   ❌ 未找到成員，相似 ID: {debug_info['similar_ids']}")
            
            # 創建模擬成員
            mock_member = NotifyDebugger.create_mock_member(scenario['member_id'])
            print(f"   🔧 創建模擬成員: {mock_member['name']}")

if __name__ == "__main__":
    print("🚀 通知調試測試開始")
    print("=" * 50)
    
    # 運行測試
    test_member_id_analysis()
    
    # 運行異步測試
    try:
        asyncio.run(test_notification_debug())
    except Exception as e:
        print(f"❌ 異步測試失敗: {e}")
    
    print("=" * 50)
    print("✨ 測試完成！") 