#!/usr/bin/env python3
"""
模擬診斷功能測試腳本
"""

import asyncio
import os
import sys

async def test_mock_diagnostic():
    """測試模擬診斷功能"""
    print("🔍 測試模擬診斷功能...")
    
    try:
        from src.diagnostic_middleware import DiagnosticMiddleware
        
        # 測試模擬資料
        print("\n1. 測試模擬資料...")
        mock_data = await DiagnosticMiddleware.get_mock_data()
        print(f"   模擬成員數量: {len(mock_data['members'])}")
        print(f"   模擬通知數量: {len(mock_data['notifications'])}")
        print(f"   模擬故事數量: {len(mock_data['stories'])}")
        
        # 測試獲取測試成員 ID（應該返回模擬 ID）
        print("\n2. 測試獲取測試成員 ID...")
        test_member_id = await DiagnosticMiddleware.get_test_member_id()
        print(f"   測試成員 ID: {test_member_id}")
        
        # 測試通知資料獲取（模擬模式）
        print("\n3. 測試通知資料獲取（模擬模式）...")
        notifications_result = await DiagnosticMiddleware.test_notifications_data(test_member_id)
        print(f"   通知測試狀態: {notifications_result['status']}")
        if notifications_result['status'] in ['success', 'success (mock)']:
            data = notifications_result['data']
            print(f"   成員 ID: {data['member_id']}")
            print(f"   通知數量: {data['notifications_count']}")
            print(f"   有資料: {data['has_data']}")
        else:
            print(f"   錯誤: {notifications_result.get('error', '未知錯誤')}")
        
        # 測試社交頁面資料獲取（模擬模式）
        print("\n4. 測試社交頁面資料獲取（模擬模式）...")
        socialpage_result = await DiagnosticMiddleware.test_socialpage_data(test_member_id)
        print(f"   社交頁面測試狀態: {socialpage_result['status']}")
        if socialpage_result['status'] in ['success', 'success (mock)']:
            data = socialpage_result['data']
            print(f"   時間戳: {data['timestamp']}")
            print(f"   故事數量: {data['stories_count']}")
            print(f"   成員數量: {data['members_count']}")
            print(f"   有資料: {data['has_data']}")
        else:
            print(f"   錯誤: {socialpage_result.get('error', '未知錯誤')}")
        
        # 測試完整診斷（模擬模式）
        print("\n5. 測試完整診斷（模擬模式）...")
        full_diagnostic = await DiagnosticMiddleware.run_full_diagnostic()
        print(f"   整體狀態: {full_diagnostic['summary']['overall_status']}")
        if full_diagnostic['summary']['issues']:
            print(f"   問題:")
            for issue in full_diagnostic['summary']['issues']:
                print(f"     - {issue}")
        else:
            print("   沒有發現問題")
        
        # 檢查 MongoDB 連接狀態
        print(f"\n6. MongoDB 連接狀態...")
        mongo_status = full_diagnostic.get('mongo_connection', {})
        print(f"   狀態: {mongo_status.get('status', 'unknown')}")
        if mongo_status.get('status') == 'error':
            print(f"   錯誤: {mongo_status.get('error', '未知錯誤')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模擬診斷測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_endpoint_simulation_mock():
    """模擬端點調用（使用模擬資料）"""
    print("\n🎯 模擬端點調用（使用模擬資料）...")
    
    try:
        # 模擬通知端點
        print("\n1. 模擬通知端點...")
        from src.diagnostic_middleware import DiagnosticMiddleware
        
        test_member_id = await DiagnosticMiddleware.get_test_member_id()
        notifications_result = await DiagnosticMiddleware.test_notifications_data(test_member_id)
        
        if notifications_result['status'] in ['success', 'success (mock)']:
            data = notifications_result['data']
            print(f"   成功獲取通知，成員 ID: {data['member_id']}")
            print(f"   通知數量: {data['notifications_count']}")
            print(f"   模式: {'模擬' if notifications_result['status'] == 'success (mock)' else '真實'}")
        else:
            print(f"   通知獲取失敗: {notifications_result.get('error', '未知錯誤')}")
        
        # 模擬社交頁面端點
        print("\n2. 模擬社交頁面端點...")
        socialpage_result = await DiagnosticMiddleware.test_socialpage_data(test_member_id)
        
        if socialpage_result['status'] in ['success', 'success (mock)']:
            data = socialpage_result['data']
            print(f"   成功獲取社交頁面")
            print(f"   故事數量: {data['stories_count']}")
            print(f"   成員數量: {data['members_count']}")
            print(f"   模式: {'模擬' if socialpage_result['status'] == 'success (mock)' else '真實'}")
        else:
            print(f"   社交頁面獲取失敗: {socialpage_result.get('error', '未知錯誤')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 端點模擬失敗: {e}")
        return False

async def main():
    """主測試函數"""
    print("🚀 模擬診斷功能測試")
    print("=" * 60)
    
    # 執行測試
    results = []
    
    # 1. 模擬診斷測試
    diagnostic_ok = await test_mock_diagnostic()
    results.append(("模擬診斷", diagnostic_ok))
    
    # 2. 端點模擬測試
    endpoint_ok = await test_endpoint_simulation_mock()
    results.append(("端點模擬", endpoint_ok))
    
    # 輸出結果摘要
    print(f"\n📋 測試結果摘要")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {test_name}: {status}")
    
    # 使用建議
    print(f"\n💡 使用建議")
    print("=" * 60)
    print("   1. 即使沒有 MongoDB，你也可以測試診斷功能")
    print("   2. 模擬模式會自動啟用當 MongoDB 連接失敗時")
    print("   3. 啟動應用後，訪問 /diagnostic 端點進行診斷")
    print("   4. 模擬資料會顯示 'success (mock)' 狀態")
    print("   5. 這可以幫助你驗證診斷邏輯是否正確")
    
    print("\n✨ 測試完成!")

if __name__ == "__main__":
    asyncio.run(main()) 