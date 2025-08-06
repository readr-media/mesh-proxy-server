# notify.py 單元測試說明

## 概述

這個目錄包含了 `src/notify.py` 中 `get_notifies` 函數的完整單元測試。測試覆蓋了各種邊界情況和錯誤處理。

## 測試文件

- `test_notify.py` - 主要的測試文件
- `run_notify_tests.py` - 測試運行腳本

## 測試覆蓋範圍

### 1. 環境變數測試
- **test_get_notifies_without_gql_endpoint**: 測試沒有設置 `MESH_GQL_ENDPOINT` 環境變數的情況

### 2. 數據庫連接測試
- **test_get_notifies_mongodb_connection_failed**: 測試 MongoDB 連接失敗的情況
- **test_get_notifies_no_record_found**: 測試沒有找到通知記錄的情況

### 3. 通知類型測試
- **test_get_notifies_with_payment_notifications**: 測試支付通知的處理
- **test_get_notifies_with_single_notification**: 測試單個通知的處理
- **test_get_notifies_with_aggregate_notification**: 測試聚合通知的處理

### 4. 數據完整性測試
- **test_get_notifies_with_missing_member**: 測試成員信息缺失的情況
- **test_get_notifies_with_content_field**: 測試包含 content 字段的通知

### 5. 功能測試
- **test_get_notifies_with_pagination**: 測試分頁功能

### 6. 錯誤處理測試
- **test_get_notifies_gql_query_error**: 測試 GQL 查詢錯誤的情況
- **test_get_notifies_exception_handling**: 測試異常處理

## 運行測試

### 方法 1: 使用 unittest 模組
```bash
python -m unittest test_notify.py -v
```

### 方法 2: 使用測試腳本
```bash
python run_notify_tests.py
```

## 測試依賴

測試使用了以下 Python 模組：
- `unittest` - Python 內建的測試框架
- `unittest.mock` - 用於模擬對象和函數
- `os` - 環境變數操作
- `copy` - 深拷貝操作

## 測試數據結構

### 模擬 MongoDB 記錄結構
```python
{
    "_id": "member_id",
    "lrt": 1234567890,  # 最後讀取時間
    "notifies": [
        {
            "uuid": "notification_uuid",
            "action": "follow|like|comment|notify_transaction",
            "from": "member_id" | ["member_id1", "member_id2"],
            "aggregate": True|False,
            "objective": "member|story|payment",
            "targetId": "target_id",
            "read": True|False,
            "ts": 1234567890,
            "content": "optional_content"  # 可選字段
        }
    ]
}
```

### 模擬 GQL 查詢結果結構
```python
{
    "members": [
        {
            "id": "member_id",
            "customId": "custom_id",
            "name": "member_name",
            "avatar": "avatar_url"
        }
    ]
}
```

## 測試驗證點

每個測試都會驗證：

1. **返回值結構**: 確保返回的通知結構正確
2. **數據完整性**: 確保通知數據沒有丟失
3. **錯誤處理**: 確保異常情況被正確處理
4. **函數調用**: 確保相關函數被正確調用
5. **邊界條件**: 確保極端情況被正確處理

## 注意事項

1. 測試使用了 Mock 對象來模擬外部依賴（MongoDB、GQL）
2. 測試會自動清理環境變數
3. 所有測試都是獨立的，不會相互影響
4. 測試覆蓋了 `get_notifies` 函數的所有主要分支

## 擴展測試

如果需要添加新的測試案例，請：

1. 在 `TestGetNotifies` 類中添加新的測試方法
2. 使用描述性的方法名稱（以 `test_` 開頭）
3. 添加適當的文檔字符串
4. 確保測試覆蓋新的功能或邊界情況 