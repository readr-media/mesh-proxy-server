#!/usr/bin/env python3
"""
最新新聞效能優化測試腳本
比較原始版本和優化版本的效能差異
"""

import asyncio
import time
import json
from datetime import datetime
import os
import sys

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_original_latest_stories():
    """測試原始最新新聞版本"""
    print("🔍 測試原始最新新聞版本...")
    
    from src.proxy import latest_stories_proxy
    from src.request_body import LatestStories
    
    start_time = time.time()
    
    # 測試數據
    test_request = LatestStories(
        publishers=["test_publisher_1", "test_publisher_2"],
        category="news",
        index=0,
        take=10
    )
    
    # 執行測試
    response = await latest_stories_proxy(test_request)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ 原始版本完成，耗時: {duration:.3f} 秒")
    print(f"   - 故事數量: {response.get('num_stories', 0)} 個")
    print(f"   - 更新時間: {response.get('update_time', 0)}")
    print(f"   - 過期時間: {response.get('expire_time', 0)}")
    
    return duration, response

async def test_optimized_latest_stories():
    """測試優化最新新聞版本"""
    print("🚀 測試優化最新新聞版本...")
    
    from src.latest_stories_optimized import get_latest_stories_optimized
    
    start_time = time.time()
    
    # 測試數據
    publishers = ["test_publisher_1", "test_publisher_2"]
    category = "news"
    
    # 執行測試
    response = await get_latest_stories_optimized(
        publishers=publishers,
        category=category,
        index=0,
        take=10
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ 優化版本完成，耗時: {duration:.3f} 秒")
    print(f"   - 故事數量: {response.get('num_stories', 0)} 個")
    print(f"   - 更新時間: {response.get('update_time', 0)}")
    print(f"   - 過期時間: {response.get('expire_time', 0)}")
    print(f"   - 快取資訊: {response.get('cache_info', {})}")
    
    return duration, response

async def test_optimized_with_monitoring():
    """測試帶監控的優化版本"""
    print("📊 測試帶監控的優化版本...")
    
    from src.latest_stories_optimized import get_latest_stories_optimized
    from src.performance_monitor import PerformanceMonitor, log_performance_detailed_async
    
    start_time = time.time()
    
    # 建立監控器
    monitor = PerformanceMonitor("test_latest_stories_with_monitoring")
    monitor.start()
    
    # 測試數據
    publishers = ["test_publisher_1", "test_publisher_2"]
    category = "news"
    
    # 執行測試
    response = await get_latest_stories_optimized(
        publishers=publishers,
        category=category,
        index=0,
        take=10,
        monitor=monitor
    )
    
    # 結束監控
    monitor.end()
    await log_performance_detailed_async(monitor)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ 帶監控的優化版本完成，耗時: {duration:.3f} 秒")
    print(f"   - 故事數量: {response.get('num_stories', 0)} 個")
    print(f"   - 快取資訊: {response.get('cache_info', {})}")
    
    return duration, response

async def test_cache_status():
    """測試快取狀態檢查"""
    print("💾 測試快取狀態檢查...")
    
    from src.latest_stories_optimized import get_cache_status
    
    publishers = ["test_publisher_1", "test_publisher_2"]
    category = "news"
    
    try:
        cache_status = await get_cache_status(publishers, category)
        
        print(f"✅ 快取狀態檢查完成")
        print(f"   - 發布者: {cache_status.get('publishers', [])}")
        print(f"   - 類別: {cache_status.get('category', '')}")
        print(f"   - 快取鍵: {cache_status.get('cache_keys', [])}")
        print(f"   - 背景任務: {cache_status.get('background_tasks', [])}")
        print(f"   - 配置: {cache_status.get('config', {})}")
        
        # 顯示快取狀態詳情
        for status in cache_status.get('cache_status', []):
            print(f"   - 快取 {status.get('key', '')}: {status.get('status', '')}")
            if status.get('age') is not None:
                print(f"     年齡: {status.get('age', 0):.1f} 秒")
        
        return cache_status
        
    except Exception as e:
        print(f"❌ 快取狀態檢查失敗: {e}")
        return None

async def test_force_update():
    """測試強制更新功能"""
    print("🔄 測試強制更新功能...")
    
    from src.latest_stories_optimized import force_update_stories
    
    publishers = ["test_publisher_1", "test_publisher_2"]
    category = "news"
    
    try:
        start_time = time.time()
        await force_update_stories(publishers, category)
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ 強制更新完成，耗時: {duration:.3f} 秒")
        print(f"   - 發布者: {publishers}")
        print(f"   - 類別: {category}")
        
        return duration
        
    except Exception as e:
        print(f"❌ 強制更新失敗: {e}")
        return None

async def test_concurrent_requests():
    """測試併發請求"""
    print("⚡ 測試併發請求...")
    
    from src.latest_stories_optimized import get_latest_stories_optimized
    
    publishers = ["test_publisher_1", "test_publisher_2"]
    category = "news"
    
    # 建立多個併發請求
    async def single_request():
        return await get_latest_stories_optimized(
            publishers=publishers,
            category=category,
            index=0,
            take=10
        )
    
    # 執行 5 個併發請求
    start_time = time.time()
    tasks = [single_request() for _ in range(5)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()
    
    total_duration = end_time - start_time
    successful_requests = len([r for r in results if not isinstance(r, Exception)])
    
    print(f"✅ 併發請求測試完成")
    print(f"   - 總耗時: {total_duration:.3f} 秒")
    print(f"   - 成功請求: {successful_requests}/5")
    print(f"   - 平均每個請求: {total_duration/5:.3f} 秒")
    
    return total_duration, successful_requests

async def main():
    """主測試函數"""
    print("=" * 60)
    print("🔬 最新新聞效能優化測試")
    print("=" * 60)
    
    # 檢查環境變數
    required_env_vars = [
        'REDIS_ENDPOINT',
        'MESH_GQL_ENDPOINT'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"❌ 缺少必要的環境變數: {missing_vars}")
        print("請設定這些環境變數後再執行測試")
        return
    
    try:
        # 測試原始版本
        original_duration, original_response = await test_original_latest_stories()
        
        print("\n" + "-" * 40)
        
        # 測試優化版本
        optimized_duration, optimized_response = await test_optimized_latest_stories()
        
        print("\n" + "-" * 40)
        
        # 測試帶監控的版本
        monitored_duration, monitored_response = await test_optimized_with_monitoring()
        
        print("\n" + "-" * 40)
        
        # 測試快取狀態
        cache_status = await test_cache_status()
        
        print("\n" + "-" * 40)
        
        # 測試強制更新
        force_update_duration = await test_force_update()
        
        print("\n" + "-" * 40)
        
        # 測試併發請求
        concurrent_duration, successful_requests = await test_concurrent_requests()
        
        print("\n" + "=" * 60)
        print("📈 效能比較結果")
        print("=" * 60)
        
        # 計算改善百分比
        if original_duration > 0:
            improvement = ((original_duration - optimized_duration) / original_duration) * 100
            print(f"🚀 優化版本改善: {improvement:.1f}%")
            print(f"   - 原始版本: {original_duration:.3f} 秒")
            print(f"   - 優化版本: {optimized_duration:.3f} 秒")
        
        # 併發效能
        if concurrent_duration > 0:
            print(f"⚡ 併發效能:")
            print(f"   - 5個併發請求總時間: {concurrent_duration:.3f} 秒")
            print(f"   - 平均每個請求: {concurrent_duration/5:.3f} 秒")
            print(f"   - 成功率: {successful_requests/5*100:.1f}%")
        
        # 快取配置資訊
        if optimized_response and 'cache_info' in optimized_response:
            cache_info = optimized_response['cache_info']
            print(f"💾 快取配置:")
            print(f"   - 快取 TTL: {cache_info.get('cache_ttl', 0)} 秒")
            print(f"   - 過期時間: {cache_info.get('expire_time_seconds', 0)} 秒")
            print(f"   - 背景更新: {'啟用' if cache_info.get('background_update_enabled', False) else '停用'}")
        
        print("\n✅ 測試完成！")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 