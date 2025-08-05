# MongoDB 診斷功能使用指南

## 概述

我們已經將診斷工具整合到應用中，可以幫助你快速識別和解決 MongoDB 連接池優化後可能出現的問題。

## 診斷端點

### 1. 完整診斷端點
```
GET /diagnostic
```

**功能：**
- 檢查 MongoDB 連接狀態
- 測試通知端點功能
- 測試社交頁面端點功能
- 比較舊版和新版資料獲取
- 提供整體健康狀態報告

**回應範例：**
```json
{
  "timestamp": 1234567890.123,
  "mongo_connection": {
    "status": "connected",
    "details": {
      "database": "dev",
      "collections": ["members", "notifications", "stories"],
      "collection_counts": {
        "members": 1000,
        "notifications": 500,
        "stories": 2000
      }
    }
  },
  "test_member_id": "member123",
  "notifications_test": {
    "status": "success",
    "data": {
      "member_id": "member123",
      "notifications_count": 5,
      "has_data": true
    }
  },
  "socialpage_test": {
    "status": "success",
    "data": {
      "timestamp": 1234567890,
      "stories_count": 10,
      "members_count": 3,
      "has_data": true
    }
  },
  "summary": {
    "overall_status": "healthy",
    "issues": []
  }
}
```

### 2. MongoDB 連接檢查端點
```
GET /diagnostic/mongo
```

**功能：**
- 僅檢查 MongoDB 連接狀態
- 檢查資料庫集合和文檔數量
- 快速診斷連接問題

## 錯誤處理改進

### 通知端點錯誤處理
當 `/notifications` 端點出現錯誤時，會返回詳細的診斷信息：

```json
{
  "error": "通知獲取失敗: MongoDB connection failed",
  "diagnostic": {
    "mongo_connection": {
      "status": "error",
      "error": "Connection timeout"
    },
    "member_id": "member123",
    "suggestion": "請檢查 /diagnostic 端點獲取詳細診斷信息"
  }
}
```

### 社交頁面端點錯誤處理
當 `/socialpage` 端點出現錯誤時，同樣會返回診斷信息。

## 使用方法

### 1. 啟動應用後進行診斷
```bash
# 啟動應用
python main.py

# 在另一個終端中檢查診斷
curl http://localhost:8000/diagnostic
```

### 2. 檢查特定問題
```bash
# 僅檢查 MongoDB 連接
curl http://localhost:8000/diagnostic/mongo

# 檢查特定端點是否正常工作
curl -X POST http://localhost:8000/notifications \
  -H "Content-Type: application/json" \
  -d '{"member_id": "test_member", "index": 0, "take": 10}'
```

### 3. 使用診斷腳本
```bash
# 運行診斷測試腳本
python test_diagnostic.py

# 運行 MongoDB 連接池測試
python test_mongo_pool.py
```

## 常見問題診斷

### 1. MongoDB 連接失敗
**症狀：** `/diagnostic/mongo` 返回 `"status": "error"`

**可能原因：**
- `MONGO_URL` 環境變數未設定或錯誤
- MongoDB 服務器未運行
- 網路連接問題
- 認證問題

**解決方案：**
```bash
# 檢查環境變數
echo $MONGO_URL

# 檢查 MongoDB 服務器狀態
# 根據你的部署方式檢查
```

### 2. 資料獲取失敗
**症狀：** 端點返回 500 錯誤，包含診斷信息

**可能原因：**
- 資料庫中沒有測試資料
- 集合名稱不正確
- 資料庫權限問題

**解決方案：**
```bash
# 檢查資料庫內容
# 使用 MongoDB 客戶端連接資料庫
mongo $MONGO_URL

# 檢查集合
show collections

# 檢查文檔數量
db.members.count()
db.notifications.count()
db.stories.count()
```

### 3. 新舊版本比較失敗
**症狀：** 比較測試返回錯誤

**可能原因：**
- 舊版函數依賴的模組有問題
- 資料格式不一致

**解決方案：**
- 檢查舊版函數的依賴
- 確保資料格式一致

## 效能監控

### 1. 連接池狀態
診斷工具會檢查連接池的配置和狀態：

```json
{
  "mongo_connection": {
    "status": "connected",
    "details": {
      "database": "dev",
      "collections": ["members", "notifications", "stories"]
    }
  }
}
```

### 2. 資料獲取效能
比較舊版和新版的資料獲取效能：

```json
{
  "comparison_test": {
    "status": "success",
    "comparison": {
      "old_notifications": {"status": "success"},
      "new_notifications": {"status": "success"}
    }
  }
}
```

## 最佳實踐

### 1. 定期診斷
- 在部署前運行診斷
- 在出現問題時立即診斷
- 定期檢查系統健康狀態

### 2. 監控關鍵指標
- MongoDB 連接狀態
- 資料獲取成功率
- 端點響應時間

### 3. 錯誤處理
- 使用診斷信息快速定位問題
- 根據建議進行修復
- 記錄診斷結果以便追蹤

## 故障排除流程

1. **檢查基本連接**
   ```bash
   curl http://localhost:8000/diagnostic/mongo
   ```

2. **檢查完整狀態**
   ```bash
   curl http://localhost:8000/diagnostic
   ```

3. **測試特定端點**
   ```bash
   curl -X POST http://localhost:8000/notifications \
     -H "Content-Type: application/json" \
     -d '{"member_id": "test_member", "index": 0, "take": 10}'
   ```

4. **查看錯誤日誌**
   - 檢查應用日誌
   - 檢查 MongoDB 日誌

5. **根據診斷結果修復**
   - 修復連接問題
   - 修復資料問題
   - 修復配置問題

## 總結

診斷功能已經完全整合到應用中，提供了：

- **即時診斷**：通過 HTTP 端點進行診斷
- **詳細錯誤信息**：包含診斷信息的錯誤回應
- **效能比較**：比較舊版和新版的效能
- **健康監控**：整體系統健康狀態報告

使用這些工具，你可以快速識別和解決 MongoDB 連接池優化後可能出現的問題，確保應用正常運行。 