# Cloud Build 變數名稱修復

## 🚨 問題描述

在 Cloud Build 配置中使用了 `TEST_EXIT_CODE` 作為變數名，但這個名稱與 Cloud Build 的內建替換變數衝突，導致錯誤：

```
generic::invalid_argument: invalid value for 'build.substitutions': key in the template "TEST_EXIT_CODE" is not a valid built-in substitution
```

## 🔧 修復方案

### 問題原因
Cloud Build 有預定義的內建替換變數，使用 `TEST_EXIT_CODE` 會與系統變數衝突。

### 修復內容
將變數名從 `TEST_EXIT_CODE` 改為 `PYTHON_TEST_EXIT_CODE`：

```yaml
# 修復前（有問題）
python run_all_tests.py
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo "✅ 所有測試通過！"
else
  echo "❌ 測試失敗！退出碼: $TEST_EXIT_CODE"
  exit $TEST_EXIT_CODE
fi

# 修復後（正確）
python run_all_tests.py
PYTHON_TEST_EXIT_CODE=$?

if [ $PYTHON_TEST_EXIT_CODE -eq 0 ]; then
  echo "✅ 所有測試通過！"
else
  echo "❌ 測試失敗！退出碼: $PYTHON_TEST_EXIT_CODE"
  exit $PYTHON_TEST_EXIT_CODE
fi
```

## ✅ 修復結果

- **變數名稱**: 使用 `PYTHON_TEST_EXIT_CODE` 避免衝突
- **功能保持**: 測試失敗處理邏輯完全保持不變
- **Cloud Build 兼容**: 不再與內建變數衝突

## 🎯 最佳實踐

在 Cloud Build 配置中命名變數時：
1. **避免使用常見前綴**: 如 `TEST_`, `BUILD_`, `PROJECT_` 等
2. **使用描述性名稱**: 如 `PYTHON_TEST_EXIT_CODE` 比 `TEST_EXIT_CODE` 更明確
3. **檢查內建變數**: 參考 Cloud Build 文檔中的內建替換變數列表

修復完成後，Cloud Build 配置應該能夠正常工作！ 