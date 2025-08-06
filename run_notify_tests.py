#!/usr/bin/env python3
"""
運行 notify.py 的單元測試
"""

import unittest
import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_tests():
    """運行所有 notify 相關的測試"""
    print("🧪 開始運行 notify.py 的單元測試...")
    print("=" * 50)
    
    # 載入測試模組
    from test_notify import TestGetNotifies
    
    # 創建測試套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestGetNotifies)
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("=" * 50)
    if result.wasSuccessful():
        print("✅ 所有測試都通過了！")
        return 0
    else:
        print("❌ 有些測試失敗了")
        return 1

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code) 