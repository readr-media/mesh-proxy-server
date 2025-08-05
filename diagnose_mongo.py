#!/usr/bin/env python3
"""
MongoDB 連接和資料診斷工具
"""

import asyncio
import os
import sys
from src.mongo_client import initialize_mongo, get_mongo_manager, close_mongo

async def diagnose_mongo_connection():
    """診斷 MongoDB 連接"""
    print("🔍 MongoDB 連接診斷")
    print("=" * 50)
    
    # 檢查環境變數
    mongo_url = os.environ.get('MONGO_URL')
    env = os.environ.get('ENV', 'dev')
    
    print(f"📋 環境變數檢查:")
    print(f"   MONGO_URL: {mongo_url}")
    print(f"   ENV: {env}")
    
    if not mongo_url:
        print("❌ MONGO_URL 未設定！")
        return False
    
    try:
        # 初始化連接
        print(f"\n🔌 嘗試連接 MongoDB...")
        await initialize_mongo(mongo_url, env)
        
        # 獲取管理器
        manager = await get_mongo_manager()
        db = manager.get_async_db()
        
        print("✅ MongoDB 連接成功！")
        
        # 檢查資料庫集合
        print(f"\n📊 檢查資料庫集合...")
        collections = await db.list_collection_names()
        print(f"   可用集合: {collections}")
        
        # 檢查 members 集合
        if 'members' in collections:
            members_count = await db.members.count_documents({})
            print(f"   members 集合文檔數量: {members_count}")
            
            # 嘗試獲取一個成員
            if members_count > 0:
                member = await db.members.find_one({})
                print(f"   範例成員 ID: {member.get('_id', 'N/A')}")
                print(f"   範例成員名稱: {member.get('name', 'N/A')}")
        
        # 檢查 notifications 集合
        if 'notifications' in collections:
            notifications_count = await db.notifications.count_documents({})
            print(f"   notifications 集合文檔數量: {notifications_count}")
        
        # 檢查 stories 集合
        if 'stories' in collections:
            stories_count = await db.stories.count_documents({})
            print(f"   stories 集合文檔數量: {stories_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB 連接失敗: {e}")
        return False
    finally:
        await close_mongo()

async def test_notifications_endpoint():
    """測試通知端點功能"""
    print(f"\n🔔 測試通知端點功能")
    print("=" * 50)
    
    try:
        # 初始化連接
        mongo_url = os.environ.get('MONGO_URL')
        env = os.environ.get('ENV', 'dev')
        await initialize_mongo(mongo_url, env)
        
        # 獲取管理器
        manager = await get_mongo_manager()
        db = manager.get_async_db()
        
        # 尋找一個有通知的成員
        member_with_notifications = await db.notifications.find_one({})
        
        if member_with_notifications:
            member_id = member_with_notifications['_id']
            print(f"   找到成員 ID: {member_id}")
            
            # 測試通知獲取
            from src.notify_optimized import get_notifies_optimized
            notifications = await get_notifies_optimized(member_id, 0, 10)
            
            print(f"   成功獲取通知:")
            print(f"     成員 ID: {notifications.get('id')}")
            print(f"     通知數量: {len(notifications.get('notifies', []))}")
            print(f"     LRT: {notifications.get('lrt')}")
            
            return True
        else:
            print("   沒有找到任何通知記錄")
            return False
            
    except Exception as e:
        print(f"❌ 通知端點測試失敗: {e}")
        return False
    finally:
        await close_mongo()

async def test_socialpage_endpoint():
    """測試社交頁面端點功能"""
    print(f"\n👥 測試社交頁面端點功能")
    print("=" * 50)
    
    try:
        # 初始化連接
        mongo_url = os.environ.get('MONGO_URL')
        env = os.environ.get('ENV', 'dev')
        await initialize_mongo(mongo_url, env)
        
        # 獲取管理器
        manager = await get_mongo_manager()
        db = manager.get_async_db()
        
        # 尋找一個有追蹤的成員
        member_with_following = await db.members.find_one({
            "following": {"$exists": True, "$ne": []}
        })
        
        if member_with_following:
            member_id = member_with_following['_id']
            following_count = len(member_with_following.get('following', []))
            print(f"   找到成員 ID: {member_id}")
            print(f"   追蹤數量: {following_count}")
            
            # 測試社交頁面獲取
            from src.socialpage_optimized import getSocialPage_optimized
            social_page = await getSocialPage_optimized(member_id, 0, 10)
            
            print(f"   成功獲取社交頁面:")
            print(f"     時間戳: {social_page.get('timestamp')}")
            print(f"     故事數量: {len(social_page.get('stories', []))}")
            print(f"     成員數量: {len(social_page.get('members', []))}")
            
            return True
        else:
            print("   沒有找到有追蹤的成員")
            return False
            
    except Exception as e:
        print(f"❌ 社交頁面端點測試失敗: {e}")
        return False
    finally:
        await close_mongo()

async def compare_old_vs_new():
    """比較舊版和新版的資料獲取"""
    print(f"\n🔄 比較舊版和新版資料獲取")
    print("=" * 50)
    
    try:
        # 初始化連接
        mongo_url = os.environ.get('MONGO_URL')
        env = os.environ.get('ENV', 'dev')
        await initialize_mongo(mongo_url, env)
        
        # 獲取管理器
        manager = await get_mongo_manager()
        db = manager.get_async_db()
        
        # 尋找一個測試成員
        test_member = await db.members.find_one({})
        if not test_member:
            print("   沒有找到測試成員")
            return False
            
        member_id = test_member['_id']
        print(f"   測試成員 ID: {member_id}")
        
        # 測試舊版通知獲取
        print(f"\n   測試舊版通知獲取...")
        try:
            from src.notify import get_notifies
            from src.socialpage import connect_db
            
            # 使用舊版同步連接
            old_db = connect_db(mongo_url, env)
            old_notifications = get_notifies(old_db, member_id, 0, 10)
            print(f"     舊版通知獲取成功")
        except Exception as e:
            print(f"     舊版通知獲取失敗: {e}")
        
        # 測試新版通知獲取
        print(f"\n   測試新版通知獲取...")
        try:
            from src.notify_optimized import get_notifies_optimized
            new_notifications = await get_notifies_optimized(member_id, 0, 10)
            print(f"     新版通知獲取成功")
        except Exception as e:
            print(f"     新版通知獲取失敗: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 比較測試失敗: {e}")
        return False
    finally:
        await close_mongo()

async def main():
    """主診斷函數"""
    print("🚀 MongoDB 診斷工具")
    print("=" * 60)
    
    # 檢查環境變數
    if not os.environ.get('MONGO_URL'):
        print("❌ 錯誤: 未設定 MONGO_URL 環境變數")
        print("   請設定 MONGO_URL 環境變數後再執行")
        return
    
    # 執行診斷
    results = []
    
    # 1. 連接診斷
    connection_ok = await diagnose_mongo_connection()
    results.append(("連接診斷", connection_ok))
    
    if connection_ok:
        # 2. 通知端點測試
        notifications_ok = await test_notifications_endpoint()
        results.append(("通知端點", notifications_ok))
        
        # 3. 社交頁面端點測試
        socialpage_ok = await test_socialpage_endpoint()
        results.append(("社交頁面端點", socialpage_ok))
        
        # 4. 比較測試
        compare_ok = await compare_old_vs_new()
        results.append(("比較測試", compare_ok))
    
    # 輸出結果摘要
    print(f"\n📋 診斷結果摘要")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {test_name}: {status}")
    
    # 建議
    print(f"\n💡 建議")
    print("=" * 60)
    
    if not connection_ok:
        print("   1. 檢查 MONGO_URL 是否正確")
        print("   2. 確認 MongoDB 服務器是否運行")
        print("   3. 檢查網路連接")
    
    if connection_ok and not any([notifications_ok, socialpage_ok]):
        print("   1. 檢查資料庫中是否有測試資料")
        print("   2. 確認集合名稱是否正確")
        print("   3. 檢查資料庫權限")
    
    print("\n✨ 診斷完成!")

if __name__ == "__main__":
    asyncio.run(main()) 