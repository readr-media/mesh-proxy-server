#!/usr/bin/env python3
"""
MongoDB 連接池效能測試腳本
"""

import asyncio
import time
import pymongo
import motor.motor_asyncio
import os
from src.mongo_client import MongoManager, initialize_mongo, close_mongo

# 設定測試環境
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
TEST_ENV = os.environ.get('ENV', 'dev')

async def test_optimized_mongo_manager():
    """測試優化的 MongoDB 管理器"""
    print("🔧 測試優化的 MongoDB 管理器...")
    
    # 初始化連接池
    await initialize_mongo(MONGO_URL, TEST_ENV)
    
    start_time = time.time()
    
    try:
        # 執行多次查詢來測試連接重用
        for i in range(10):
            from src.mongo_client import get_mongo_manager
            manager = await get_mongo_manager()
            db = manager.get_async_db()
            
            # 執行一個簡單的查詢
            result = await db.members.find_one({})
            print(f"  查詢 {i+1}: 成功")
            
        total_time = time.time() - start_time
        avg_time = total_time / 10
        print(f"✅ 優化管理器 - 總時間: {total_time:.3f}s, 平均: {avg_time:.3f}s")
        
    except Exception as e:
        print(f"❌ 優化管理器錯誤: {e}")
    finally:
        await close_mongo()
    
    return total_time

def test_traditional_pymongo():
    """測試傳統的 pymongo 連接"""
    print("📡 測試傳統 pymongo 連接...")
    
    start_time = time.time()
    
    try:
        # 執行多次查詢，每次都建立新連接
        for i in range(10):
            client = pymongo.MongoClient(MONGO_URL)
            if TEST_ENV == 'staging':
                db = client.staging
            elif TEST_ENV == 'prod':
                db = client.prod
            else:
                db = client.dev
            
            # 執行一個簡單的查詢
            result = db.members.find_one({})
            client.close()
            print(f"  查詢 {i+1}: 成功")
            
        total_time = time.time() - start_time
        avg_time = total_time / 10
        print(f"📊 傳統 pymongo - 總時間: {total_time:.3f}s, 平均: {avg_time:.3f}s")
        
    except Exception as e:
        print(f"❌ 傳統 pymongo 錯誤: {e}")
        return None
    
    return total_time

async def test_direct_motor():
    """測試直接使用 motor"""
    print("⚡ 測試直接 motor...")
    
    start_time = time.time()
    
    try:
        # 建立一個 motor 客戶端
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
        if TEST_ENV == 'staging':
            db = client.staging
        elif TEST_ENV == 'prod':
            db = client.prod
        else:
            db = client.dev
        
        # 執行多次查詢
        for i in range(10):
            result = await db.members.find_one({})
            print(f"  查詢 {i+1}: 成功")
        
        client.close()
        total_time = time.time() - start_time
        avg_time = total_time / 10
        print(f"🚀 直接 motor - 總時間: {total_time:.3f}s, 平均: {avg_time:.3f}s")
        
    except Exception as e:
        print(f"❌ 直接 motor 錯誤: {e}")
        return None
    
    return total_time

async def test_connection_pool_stats():
    """測試連接池統計資訊"""
    print("📊 測試連接池統計資訊...")
    
    try:
        await initialize_mongo(MONGO_URL, TEST_ENV)
        
        from src.mongo_client import get_mongo_manager
        manager = await get_mongo_manager()
        
        # 獲取連接池統計資訊
        async_client = manager.get_async_client()
        sync_client = manager.get_sync_client()
        
        print(f"  非同步客戶端連接池大小: {async_client.options.max_pool_size}")
        print(f"  同步客戶端連接池大小: {sync_client.options.max_pool_size}")
        
        # 執行一些查詢來測試連接池
        db = manager.get_async_db()
        for i in range(5):
            await db.members.find_one({})
            print(f"  測試查詢 {i+1}: 完成")
        
        await close_mongo()
        print("✅ 連接池統計測試完成")
        
    except Exception as e:
        print(f"❌ 連接池統計測試錯誤: {e}")

async def main():
    """主測試函數"""
    print("🚀 MongoDB 連接池效能測試")
    print("=" * 50)
    
    # 檢查環境變數
    if not os.environ.get('MONGO_URL'):
        print("⚠️  警告: 未設定 MONGO_URL 環境變數")
        print("   使用預設值: mongodb://localhost:27017")
    
    print(f"🎯 測試目標: {MONGO_URL}")
    print(f"🌍 環境: {TEST_ENV}")
    print()
    
    # 執行測試
    results = {}
    
    # 測試連接池統計
    await test_connection_pool_stats()
    print()
    
    # 測試優化的 MongoDB 管理器
    optimized_time = await test_optimized_mongo_manager()
    if optimized_time:
        results['optimized'] = optimized_time
    
    print()
    
    # 測試傳統 pymongo
    traditional_time = test_traditional_pymongo()
    if traditional_time:
        results['traditional'] = traditional_time
    
    print()
    
    # 測試直接 motor
    motor_time = await test_direct_motor()
    if motor_time:
        results['motor'] = motor_time
    
    print()
    print("📊 效能比較結果:")
    print("=" * 50)
    
    if len(results) >= 2:
        fastest = min(results, key=results.get)
        slowest = max(results, key=results.get)
        
        for method, time_taken in results.items():
            improvement = ""
            if method != fastest:
                improvement_pct = ((results[slowest] - time_taken) / results[slowest]) * 100
                improvement = f" (改善 {improvement_pct:.1f}%)"
            
            print(f"{method:12}: {time_taken:.3f}s{improvement}")
        
        print(f"\n🏆 最快方法: {fastest}")
        print(f"🐌 最慢方法: {slowest}")
        
        if 'optimized' in results and 'traditional' in results:
            improvement = ((results['traditional'] - results['optimized']) / results['traditional']) * 100
            print(f"💡 優化管理器相比傳統連接改善: {improvement:.1f}%")
    
    print("\n✨ 測試完成!")

if __name__ == "__main__":
    asyncio.run(main()) 