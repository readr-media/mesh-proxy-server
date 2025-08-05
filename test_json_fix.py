#!/usr/bin/env python3
"""
測試 JSON 修復是否有效
"""

def test_json_fix():
    """測試 JSON 修復是否有效"""
    print("🧪 測試 JSON 修復...")
    
    # 確保 json_optimizer 被導入
    import src.json_optimizer
    import json
    
    # 測試資料
    test_data = {
        "chinese": "中文測試",
        "emoji": "🚀🎉✨",
        "unicode": "café résumé naïve"
    }
    
    # 測試 1: ensure_ascii=False（orjson 支援）
    print("1. 測試 ensure_ascii=False...")
    try:
        result = json.dumps(test_data, ensure_ascii=False)
        print(f"   ✅ ensure_ascii=False 正常工作，結果長度: {len(result)}")
        print(f"   結果: {result[:50]}...")
    except Exception as e:
        print(f"   ❌ ensure_ascii=False 錯誤: {e}")
        return False
    
    # 測試 2: ensure_ascii=True（需要回退到標準 json）
    print("2. 測試 ensure_ascii=True...")
    try:
        result = json.dumps(test_data, ensure_ascii=True)
        print(f"   ✅ ensure_ascii=True 正常工作，結果長度: {len(result)}")
        print(f"   結果: {result[:50]}...")
    except Exception as e:
        print(f"   ❌ ensure_ascii=True 錯誤: {e}")
        return False
    
    # 測試 3: indent 參數（需要回退到標準 json）
    print("3. 測試 indent 參數...")
    try:
        result = json.dumps(test_data, indent=2, ensure_ascii=False)
        print(f"   ✅ indent 參數正常工作，結果長度: {len(result)}")
        print(f"   結果前幾行:\n{result[:100]}...")
    except Exception as e:
        print(f"   ❌ indent 參數錯誤: {e}")
        return False
    
    # 測試 4: sort_keys 參數（orjson 支援）
    print("4. 測試 sort_keys 參數...")
    try:
        result = json.dumps(test_data, sort_keys=True, ensure_ascii=False)
        print(f"   ✅ sort_keys 參數正常工作，結果長度: {len(result)}")
        print(f"   結果: {result[:50]}...")
    except Exception as e:
        print(f"   ❌ sort_keys 參數錯誤: {e}")
        return False
    
    # 測試 5: 複雜資料結構
    print("5. 測試複雜資料結構...")
    complex_data = {
        "users": [
            {"id": 1, "name": "張三", "active": True},
            {"id": 2, "name": "李四", "active": False}
        ],
        "metadata": {
            "created_at": "2024-01-01T00:00:00Z",
            "version": "1.0.0"
        }
    }
    
    try:
        result = json.dumps(complex_data, ensure_ascii=False, sort_keys=True)
        parsed = json.loads(result)
        print(f"   ✅ 複雜資料結構正常工作，解析結果類型: {type(parsed)}")
    except Exception as e:
        print(f"   ❌ 複雜資料結構錯誤: {e}")
        return False
    
    print("🎉 JSON 修復測試完成！")
    return True

if __name__ == "__main__":
    print("🚀 JSON 修復測試開始")
    print("=" * 50)
    
    if test_json_fix():
        print("✅ 所有測試通過！JSON 修復成功")
    else:
        print("❌ 部分測試失敗，請檢查 JSON 修復")
    
    print("=" * 50) 