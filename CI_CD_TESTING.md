# CI/CD 測試流程說明

## 概述

我們已經在 Cloud Build 中集成了完整的測試流程，確保在部署之前所有代碼都經過測試驗證。

## 測試流程

### 1. 依賴檢查
- 檢查核心依賴是否正確安裝（requests, gql, pymongo, redis）
- 檢查可選依賴（fastapi, uvicorn, firebase_admin）
- 只有核心依賴缺失才會阻止構建

### 2. 代碼風格檢查
- 使用 flake8 檢查代碼風格
- 忽略行長度限制（E501）和換行問題（W503）
- 代碼風格問題不會阻止構建，但會顯示警告

### 3. 單元測試
- 運行所有測試文件：
  - `test_notify.py` - notify.py 的單元測試
  - `test_http_pool.py` - HTTP 連接池測試
  - `test_mongo_pool.py` - MongoDB 連接池測試
  - `test_error_fix.py` - 錯誤修復測試
  - `test_mock_diagnostic.py` - 模擬診斷測試
  - `test_notification_debug.py` - 通知調試測試

## Cloud Build 配置

### 更新後的 cloudbuild.yaml

```yaml
steps:
  # 安裝依賴並運行測試
  - name: python:3.9
    id: Install Dependencies and Run Tests
    entrypoint: bash
    args:
      - '-c'
      - |
        echo "🔧 安裝 Python 依賴..."
        pip install -r requirements.txt
        
        echo "🧪 運行所有測試..."
        python run_all_tests.py
        
        echo "✅ 測試完成！"
    
  # 構建 Docker 鏡像
  - name: gcr.io/cloud-builders/docker
    id: Build Image
    args:
      - build
      - "-t"
      - "gcr.io/$PROJECT_ID/${_SERVICE_NAME}:${BRANCH_NAME}_${SHORT_SHA}"
      - .

  # 推送鏡像
  - name: gcr.io/cloud-builders/docker
    id: Push Image
    args:
      - push
      - "gcr.io/$PROJECT_ID/${_SERVICE_NAME}:${BRANCH_NAME}_${SHORT_SHA}"

  # 部署到 Cloud Run
  - name: gcr.io/cloud-builders/gcloud
    id: Deploy Image
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        IFS=',' read -r -a cloud_runs <<< "${_SERVICE_NAME}"
        for cr in "${cloud_runs[@]}"
        do
          gcloud run deploy "$cr" --image gcr.io/$PROJECT_ID/${_SERVICE_NAME}:${BRANCH_NAME}_${SHORT_SHA} --region asia-east1
        done
```

## 測試腳本

### run_all_tests.py

這個腳本提供了完整的測試流程：

1. **依賴檢查** - 確保所有必要的模組都已安裝
2. **代碼風格檢查** - 使用 flake8 檢查代碼質量
3. **單元測試** - 運行所有測試文件並統計結果

### 使用方法

```bash
# 本地運行測試
python run_all_tests.py

# 運行特定測試文件
python -m unittest test_notify.py -v

# 運行所有測試
python -m unittest discover -v
```

## 測試覆蓋範圍

### notify.py 測試
- 環境變數測試
- 數據庫連接測試
- 通知類型測試（支付、單個、聚合）
- 數據完整性測試
- 分頁功能測試
- 錯誤處理測試

### 其他測試
- HTTP 連接池測試
- MongoDB 連接池測試
- 錯誤修復測試
- 診斷功能測試
- 通知調試測試

## 構建優化

### .cloudbuildignore
我們創建了 `.cloudbuildignore` 文件來排除不必要的文件，加快構建速度：

- Git 相關文件
- Python 緩存文件
- IDE 配置文件
- 文檔文件（除了 README.md）
- 日誌和臨時文件

## 故障排除

### 常見問題

1. **依賴安裝失敗**
   - 檢查 requirements.txt 文件
   - 確保網絡連接正常
   - 檢查 Python 版本兼容性

2. **測試失敗**
   - 查看測試輸出日誌
   - 檢查 Mock 對象設置
   - 驗證測試數據結構

3. **代碼風格問題**
   - 使用 `flake8 src/` 檢查具體問題
   - 根據提示修復代碼風格

### 本地測試

在提交代碼之前，建議在本地運行測試：

```bash
# 安裝依賴
pip install -r requirements.txt

# 運行測試
python run_all_tests.py

# 檢查代碼風格
flake8 src/ --max-line-length=120 --ignore=E501,W503
```

## 最佳實踐

1. **提交前測試** - 在提交代碼前運行測試
2. **小步提交** - 每次提交包含小的、可測試的變更
3. **測試覆蓋** - 為新功能添加相應的測試
4. **代碼風格** - 保持一致的代碼風格
5. **文檔更新** - 更新相關文檔和註釋

## 監控和報告

測試結果會在 Cloud Build 日誌中顯示：

- 依賴檢查結果
- 代碼風格檢查結果
- 單元測試統計
- 最終構建狀態

如果測試失敗，構建過程會停止，不會部署有問題的代碼。 