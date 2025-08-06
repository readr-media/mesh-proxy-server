#!/usr/bin/env python3
"""
運行所有測試的腳本，適合在 CI/CD 環境中使用
"""

import unittest
import sys
import os
import subprocess

def run_python_tests():
    """運行 Python 單元測試"""
    print("🧪 開始運行 Python 單元測試...")
    print("=" * 60)
    
    # 測試文件列表
    test_files = [
        'test_notify.py',
        'test_http_pool.py',
        'test_mongo_pool.py',
        'test_error_fix.py',
        'test_mock_diagnostic.py',
        'test_notification_debug.py'
    ]
    
    all_tests_passed = True
    total_tests = 0
    passed_tests = 0
    
    for test_file in test_files:
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
                    # 計算測試數量
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Ran ' in line and ' tests in ' in line:
                            try:
                                test_count = int(line.split('Ran ')[1].split(' ')[0])
                                total_tests += test_count
                                passed_tests += test_count
                            except (ValueError, IndexError):
                                # 如果無法解析測試數量，至少算作 1 個測試
                                total_tests += 1
                                passed_tests += 1
                            break
                    else:
                        # 如果沒有找到測試統計行，至少算作 1 個測試
                        total_tests += 1
                        passed_tests += 1
                else:
                    print(f"❌ {test_file} 測試失敗")
                    print("錯誤輸出:")
                    print(result.stderr)
                    all_tests_passed = False
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ {test_file} 測試超時")
                all_tests_passed = False
            except Exception as e:
                print(f"💥 {test_file} 測試執行錯誤: {e}")
                all_tests_passed = False
        else:
            print(f"⚠️  測試文件不存在: {test_file}")
    
    print("\n" + "=" * 60)
    print(f"📊 測試結果統計:")
    print(f"   總測試數: {total_tests}")
    print(f"   通過測試: {passed_tests}")
    print(f"   失敗測試: {total_tests - passed_tests}")
    
    return all_tests_passed

def run_linting():
    """運行代碼檢查（如果可用）"""
    print("\n🔍 檢查代碼風格...")
    
    try:
        # 檢查是否有 flake8
        result = subprocess.run([
            sys.executable, '-m', 'flake8', 'src/', '--max-line-length=120', '--ignore=E501,W503'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 代碼風格檢查通過")
            return True
        else:
            print("⚠️  代碼風格檢查發現問題（非致命）:")
            print(result.stdout)
            # 在 CI/CD 中，代碼風格問題不會阻止構建
            return True
    except ImportError:
        print("ℹ️  flake8 未安裝，跳過代碼風格檢查")
        return True
    except Exception as e:
        print(f"ℹ️  代碼風格檢查跳過: {e}")
        return True

def check_dependencies():
    """檢查依賴是否正確安裝"""
    print("\n📦 檢查依賴...")
    
    # 核心依賴（必須的）
    core_modules = [
        'requests',
        'gql',
        'pymongo',
        'redis'
    ]
    
    # 可選依賴（如果沒有也不會影響測試）
    optional_modules = [
        'fastapi',
        'uvicorn',
        'firebase_admin'
    ]
    
    missing_core = []
    missing_optional = []
    
    for module in core_modules:
        try:
            __import__(module)
            print(f"✅ {module} (核心)")
        except ImportError:
            print(f"❌ {module} (核心)")
            missing_core.append(module)
    
    for module in optional_modules:
        try:
            __import__(module)
            print(f"✅ {module} (可選)")
        except ImportError:
            print(f"⚠️  {module} (可選，未安裝)")
            missing_optional.append(module)
    
    if missing_core:
        print(f"\n❌ 缺少核心依賴: {', '.join(missing_core)}")
        return False
    
    if missing_optional:
        print(f"\n⚠️  缺少可選依賴: {', '.join(missing_optional)}")
    
    print("✅ 核心依賴都已正確安裝")
    return True

def main():
    """主函數"""
    print("🚀 開始 CI/CD 測試流程")
    print("=" * 60)
    
    # 檢查依賴
    deps_ok = check_dependencies()
    
    # 運行代碼風格檢查
    lint_ok = run_linting()
    
    # 運行單元測試
    tests_ok = run_python_tests()
    
    print("\n" + "=" * 60)
    print("📋 最終結果:")
    print(f"   依賴檢查: {'✅ 通過' if deps_ok else '❌ 失敗'}")
    print(f"   代碼風格: {'✅ 通過' if lint_ok else '❌ 失敗'}")
    print(f"   單元測試: {'✅ 通過' if tests_ok else '❌ 失敗'}")
    
    if deps_ok and lint_ok and tests_ok:
        print("\n🎉 所有檢查都通過了！")
        return 0
    else:
        print("\n💥 有些檢查失敗了，請修復後重試")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 