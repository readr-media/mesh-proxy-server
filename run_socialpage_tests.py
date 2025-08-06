#!/usr/bin/env python3
"""
專門運行 socialpage.py 測試的腳本
"""

import unittest
import sys
import os
import subprocess

def run_socialpage_tests():
    """運行 socialpage 測試"""
    print("🧪 開始運行 SocialPage 測試...")
    print("=" * 60)
    
    test_file = 'test_socialpage.py'
    
    if os.path.exists(test_file):
        print(f"\n📋 運行測試文件: {test_file}")
        print("-" * 40)
        
        try:
            # 使用 unittest 運行測試
            result = subprocess.run([
                sys.executable, '-m', 'unittest', test_file, '-v'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ {test_file} 測試通過")
                print("\n📊 測試輸出:")
                print(result.stdout)
                return True
            else:
                print(f"❌ {test_file} 測試失敗")
                print("錯誤輸出:")
                print(result.stderr)
                print("標準輸出:")
                print(result.stdout)
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file} 測試超時")
            return False
        except Exception as e:
            print(f"💥 {test_file} 測試執行錯誤: {e}")
            return False
    else:
        print(f"⚠️  測試文件不存在: {test_file}")
        return False

def main():
    """主函數"""
    print("🚀 SocialPage 測試運行器")
    print("=" * 60)
    
    # 運行測試
    success = run_socialpage_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有 SocialPage 測試通過！")
        sys.exit(0)
    else:
        print("❌ SocialPage 測試失敗！")
        sys.exit(1)

if __name__ == '__main__':
    main() 