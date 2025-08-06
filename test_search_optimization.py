#!/usr/bin/env python3
"""
搜尋效能優化測試腳本
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

async def test_original_search():
    """測試原始搜尋版本"""
    print("🔍 測試原始搜尋版本...")
    
    import src.search as search_api
    
    start_time = time.time()
    
    # 建立 MeiliSearch 客戶端
    client = search_api.connect_meilisearch()
    
    # 測試搜尋
    search_text = "測試搜尋"
    
    # 順序執行各個搜尋
    stories = await search_api.search_related_stories(client, search_text)
    collections = search_api.search_related_collections(client, search_text)
    members = search_api.search_related_members(client, search_text)
    publishers = search_api.search_related_publishers(client, search_text)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ 原始版本完成，耗時: {duration:.3f} 秒")
    print(f"   - 故事: {len(stories)} 個")
    print(f"   - 集合: {len(collections)} 個")
    print(f"   - 成員: {len(members)} 個")
    print(f"   - 發布者: {len(publishers)} 個")
    
    return duration

async def test_optimized_search():
    """測試優化搜尋版本"""
    print("🚀 測試優化搜尋版本...")
    
    from src.search_optimized import search_all_optimized
    
    start_time = time.time()
    
    # 並行執行所有搜尋
    search_text = "測試搜尋"
    objectives = ["story", "collection", "member", "publisher"]
    
    results = await search_all_optimized(search_text, objectives)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ 優化版本完成，耗時: {duration:.3f} 秒")
    print(f"   - 故事: {len(results.get('story', []))} 個")
    print(f"   - 集合: {len(results.get('collection', []))} 個")
    print(f"   - 成員: {len(results.get('member', []))} 個")
    print(f"   - 發布者: {len(results.get('publisher', []))} 個")
    
    return duration

async def test_optimized_search_with_monitoring():
    """測試帶監控的優化搜尋版本"""
    print("📊 測試帶監控的優化搜尋版本...")
    
    from src.search_optimized import search_all_optimized
    from src.performance_monitor import PerformanceMonitor, log_performance_detailed_async
    
    start_time = time.time()
    
    # 建立監控器
    monitor = PerformanceMonitor("test_search_with_monitoring")
    monitor.start()
    
    # 並行執行所有搜尋
    search_text = "測試搜尋"
    objectives = ["story", "collection", "member", "publisher"]
    
    results = await search_all_optimized(search_text, objectives, monitor=monitor)
    
    # 結束監控
    monitor.end()
    await log_performance_detailed_async(monitor)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ 帶監控的優化版本完成，耗時: {duration:.3f} 秒")
    print(f"   - 故事: {len(results.get('story', []))} 個")
    print(f"   - 集合: {len(results.get('collection', []))} 個")
    print(f"   - 成員: {len(results.get('member', []))} 個")
    print(f"   - 發布者: {len(results.get('publisher', []))} 個")
    
    return duration

async def test_cache_performance():
    """測試快取效能"""
    print("💾 測試快取效能...")
    
    from src.search_optimized import search_all_optimized
    
    search_text = "快取測試"
    objectives = ["story", "collection", "member", "publisher"]
    
    # 第一次搜尋（無快取）
    print("   第一次搜尋（無快取）...")
    start_time = time.time()
    results1 = await search_all_optimized(search_text, objectives)
    first_duration = time.time() - start_time
    print(f"   耗時: {first_duration:.3f} 秒")
    
    # 第二次搜尋（有快取）
    print("   第二次搜尋（有快取）...")
    start_time = time.time()
    results2 = await search_all_optimized(search_text, objectives)
    second_duration = time.time() - start_time
    print(f"   耗時: {second_duration:.3f} 秒")
    
    # 計算快取命中率改善
    if first_duration > 0:
        improvement = ((first_duration - second_duration) / first_duration) * 100
        print(f"   🎯 快取改善: {improvement:.1f}%")
    
    return first_duration, second_duration

async def main():
    """主測試函數"""
    print("=" * 60)
    print("🔬 搜尋效能優化測試")
    print("=" * 60)
    
    # 檢查環境變數
    required_env_vars = [
        'MEILISEARCH_HOST',
        'MEILISEARCH_APIKEY',
        'MESH_GQL_ENDPOINT'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"❌ 缺少必要的環境變數: {missing_vars}")
        print("請設定這些環境變數後再執行測試")
        return
    
    try:
        # 測試原始版本
        original_duration = await test_original_search()
        
        print("\n" + "-" * 40)
        
        # 測試優化版本
        optimized_duration = await test_optimized_search()
        
        print("\n" + "-" * 40)
        
        # 測試帶監控的版本
        monitored_duration = await test_optimized_search_with_monitoring()
        
        print("\n" + "-" * 40)
        
        # 測試快取效能
        first_cache_duration, second_cache_duration = await test_cache_performance()
        
        print("\n" + "=" * 60)
        print("📈 效能比較結果")
        print("=" * 60)
        
        # 計算改善百分比
        if original_duration > 0:
            improvement = ((original_duration - optimized_duration) / original_duration) * 100
            print(f"🚀 優化版本改善: {improvement:.1f}%")
            print(f"   - 原始版本: {original_duration:.3f} 秒")
            print(f"   - 優化版本: {optimized_duration:.3f} 秒")
        
        if first_cache_duration > 0:
            cache_improvement = ((first_cache_duration - second_cache_duration) / first_cache_duration) * 100
            print(f"💾 快取改善: {cache_improvement:.1f}%")
            print(f"   - 無快取: {first_cache_duration:.3f} 秒")
            print(f"   - 有快取: {second_cache_duration:.3f} 秒")
        
        print("\n✅ 測試完成！")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 