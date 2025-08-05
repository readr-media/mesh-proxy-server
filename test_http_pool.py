#!/usr/bin/env python3
"""
HTTP 連接池效能測試腳本
"""

import asyncio
import time
import aiohttp
import requests
from src.http_client import OptimizedHTTPClient
import os

# 設定測試環境
TEST_URL = os.environ.get('MESH_GQL_ENDPOINT', 'http://localhost:4000/graphql')
TEST_DATA = {
    "query": """
    query {
        publishers {
            id
            title
        }
    }
    """
}

async def test_optimized_http_client():
    """測試優化的 HTTP 客戶端"""
    print("🔧 測試優化的 HTTP 客戶端...")
    
    client = OptimizedHTTPClient()
    start_time = time.time()
    
    try:
        # 執行多次請求來測試連接重用
        for i in range(10):
            response = await client.post_json(TEST_URL, TEST_DATA)
            print(f"  請求 {i+1}: 成功")
            
        total_time = time.time() - start_time
        avg_time = total_time / 10
        print(f"✅ 優化客戶端 - 總時間: {total_time:.3f}s, 平均: {avg_time:.3f}s")
        
    except Exception as e:
        print(f"❌ 優化客戶端錯誤: {e}")
    finally:
        await client.close()
    
    return total_time

def test_requests_library():
    """測試傳統的 requests 庫"""
    print("📡 測試傳統 requests 庫...")
    
    start_time = time.time()
    
    try:
        # 執行多次請求
        for i in range(10):
            response = requests.post(TEST_URL, json=TEST_DATA, timeout=30)
            response.raise_for_status()
            print(f"  請求 {i+1}: 成功")
            
        total_time = time.time() - start_time
        avg_time = total_time / 10
        print(f"📊 傳統 requests - 總時間: {total_time:.3f}s, 平均: {avg_time:.3f}s")
        
    except Exception as e:
        print(f"❌ 傳統 requests 錯誤: {e}")
        return None
    
    return total_time

async def test_aiohttp_direct():
    """測試直接使用 aiohttp"""
    print("⚡ 測試直接 aiohttp...")
    
    start_time = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            for i in range(10):
                async with session.post(TEST_URL, json=TEST_DATA) as response:
                    await response.json()
                print(f"  請求 {i+1}: 成功")
                
        total_time = time.time() - start_time
        avg_time = total_time / 10
        print(f"🚀 直接 aiohttp - 總時間: {total_time:.3f}s, 平均: {avg_time:.3f}s")
        
    except Exception as e:
        print(f"❌ 直接 aiohttp 錯誤: {e}")
        return None
    
    return total_time

async def main():
    """主測試函數"""
    print("🚀 HTTP 連接池效能測試")
    print("=" * 50)
    
    # 檢查環境變數
    if not os.environ.get('MESH_GQL_ENDPOINT'):
        print("⚠️  警告: 未設定 MESH_GQL_ENDPOINT 環境變數")
        print("   使用預設值: http://localhost:4000/graphql")
    
    print(f"🎯 測試目標: {TEST_URL}")
    print()
    
    # 執行測試
    results = {}
    
    # 測試優化的 HTTP 客戶端
    optimized_time = await test_optimized_http_client()
    if optimized_time:
        results['optimized'] = optimized_time
    
    print()
    
    # 測試傳統 requests
    requests_time = test_requests_library()
    if requests_time:
        results['requests'] = requests_time
    
    print()
    
    # 測試直接 aiohttp
    aiohttp_time = await test_aiohttp_direct()
    if aiohttp_time:
        results['aiohttp'] = aiohttp_time
    
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
        
        if 'optimized' in results and 'requests' in results:
            improvement = ((results['requests'] - results['optimized']) / results['requests']) * 100
            print(f"💡 優化客戶端相比 requests 改善: {improvement:.1f}%")
    
    print("\n✨ 測試完成!")

if __name__ == "__main__":
    asyncio.run(main()) 