#!/usr/bin/env python3
"""
測試錯誤修復
"""

import asyncio
import os

async def test_error_handler():
    """測試錯誤處理器"""
    print("🔧 測試錯誤處理器...")
    
    try:
        from src.error_handler import ErrorHandler
        
        # 測試 GQL 錯誤處理
        print("\n1. 測試 GQL 錯誤處理...")
        result = ErrorHandler.handle_gql_error(None, "Connection failed", "test")
        print(f"   None 結果: {result['status']}")
        
        result = ErrorHandler.handle_gql_error({"data": "test"}, None, "test")
        print(f"   有效結果: {result['status']}")
        
        # 測試安全獲取
        print("\n2. 測試安全獲取...")
        test_data = {"key1": "value1", "key2": ["item1", "item2"]}
        value1 = ErrorHandler.safe_get(test_data, "key1", "default")
        value2 = ErrorHandler.safe_get(test_data, "nonexistent", "default")
        print(f"   key1: {value1}")
        print(f"   nonexistent: {value2}")
        
        # 測試列表操作
        print("\n3. 測試列表操作...")
        list_result = ErrorHandler.safe_list_operation(["item1", "item2"], "test list")
        print(f"   有效列表: {len(list_result)} items")
        
        list_result = ErrorHandler.safe_list_operation("not a list", "test list")
        print(f"   無效列表: {len(list_result)} items")
        
        # 測試空回應創建
        print("\n4. 測試空回應創建...")
        empty_notifications = ErrorHandler.create_empty_response("notifications")
        empty_socialpage = ErrorHandler.create_empty_response("socialpage")
        print(f"   空通知: {empty_notifications}")
        print(f"   空社交頁面: {empty_socialpage}")
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤處理器測試失敗: {e}")
        return False

async def test_optimized_functions():
    """測試優化的函數"""
    print("\n🔧 測試優化的函數...")
    
    try:
        # 測試通知函數（使用模擬資料）
        print("\n1. 測試通知函數...")
        from src.diagnostic_middleware import DiagnosticMiddleware
        
        test_member_id = "mock_member_1"
        notifications_result = await DiagnosticMiddleware.test_notifications_data(test_member_id)
        print(f"   通知測試結果: {notifications_result['status']}")
        
        # 測試社交頁面函數（使用模擬資料）
        print("\n2. 測試社交頁面函數...")
        socialpage_result = await DiagnosticMiddleware.test_socialpage_data(test_member_id)
        print(f"   社交頁面測試結果: {socialpage_result['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 優化函數測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主測試函數"""
    print("🚀 錯誤修復測試")
    print("=" * 60)
    
    # 執行測試
    results = []
    
    # 1. 錯誤處理器測試
    error_handler_ok = await test_error_handler()
    results.append(("錯誤處理器", error_handler_ok))
    
    # 2. 優化函數測試
    optimized_functions_ok = await test_optimized_functions()
    results.append(("優化函數", optimized_functions_ok))
    
    # 輸出結果摘要
    print(f"\n📋 測試結果摘要")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {test_name}: {status}")
    
    # 修復總結
    print(f"\n🔧 修復總結")
    print("=" * 60)
    print("   1. 添加了 GQL 查詢結果的類型檢查")
    print("   2. 添加了 MongoDB 查詢的空值檢查")
    print("   3. 實現了統一的錯誤處理器")
    print("   4. 添加了詳細的調試日誌")
    print("   5. 改進了空回應的處理")
    
    print("\n✨ 測試完成!")

if __name__ == "__main__":
    asyncio.run(main()) 