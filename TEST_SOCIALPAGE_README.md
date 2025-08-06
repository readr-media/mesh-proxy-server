# SocialPage 測試文檔

## 概述

`test_socialpage.py` 包含了對 `src/socialpage.py` 中 `getSocialPage` 函數的全面單元測試。

## 測試覆蓋範圍

### 主要功能測試

#### 1. 緩存功能測試
- **`test_get_social_page_with_cache`**: 測試有緩存數據的情況
  - 驗證緩存數據正確返回
  - 確保不會調用數據庫查詢
  - 驗證返回數據結構正確

#### 2. 數據庫查詢測試
- **`test_get_social_page_no_cache`**: 測試沒有緩存數據的情況
  - 模擬完整的數據庫查詢流程
  - 測試 GQL 查詢、成員數據、故事數據的處理
  - 驗證推薦成員和故事排序邏輯

#### 3. 分頁功能測試
- **`test_get_social_page_with_pagination`**: 測試分頁功能
  - 驗證 `index` 和 `take` 參數的正確處理
  - 測試分頁邊界情況

#### 4. 邊界情況測試
- **`test_get_social_page_empty_following_list`**: 測試用戶沒有關注任何人的情況
- **`test_get_social_page_large_pagination`**: 測試大分頁參數的情況
- **`test_get_social_page_negative_pagination`**: 測試負數分頁參數的情況

### 錯誤處理測試

#### 1. 數據異常測試
- **`test_get_social_page_inactive_members`**: 測試非活躍成員的處理
  - 驗證 `is_active=False` 的成員被正確過濾
  - 確保不活躍成員不會出現在推薦列表中

- **`test_get_social_page_story_without_publisher`**: 測試沒有發布者的故事
  - 驗證 `publisher_id=None` 的故事被正確過濾
  - 確保無效故事不會出現在結果中

#### 2. 系統錯誤測試
- **`test_get_social_page_gql_error`**: 測試 GQL 查詢錯誤
  - 驗證 GQL 查詢失敗時的錯誤處理
  - 確保返回空的社交頁面而不是崩潰

- **`test_get_social_page_member_not_found`**: 測試成員不存在的情況
  - 驗證成員不存在時的錯誤處理
  - 確保返回空的社交頁面

- **`test_get_social_page_cache_set_error`**: 測試緩存設置失敗的情況
  - 驗證緩存設置失敗時的錯誤處理
  - 確保即使緩存失敗也能返回正確數據

### 數據庫連接測試

#### 環境配置測試
- **`test_connect_db_dev_environment`**: 測試開發環境的數據庫連接
- **`test_connect_db_prod_environment`**: 測試生產環境的數據庫連接
- **`test_connect_db_staging_environment`**: 測試測試環境的數據庫連接

## 測試數據結構

### 模擬數據類型

1. **成員數據 (Member Data)**
   ```python
   {
       "_id": "member_id",
       "name": "用戶名稱",
       "nickname": "暱稱",
       "customId": "自定義ID",
       "avatar": "頭像URL",
       "is_active": True,
       "following": ["關注的成員ID列表"],
       "story_reads": [{"sid": "故事ID", "ts": 時間戳}],
       "story_comments": [{"sid": "故事ID", "ts": 時間戳, "content": "評論內容"}]
   }
   ```

2. **故事數據 (Story Data)**
   ```python
   {
       "_id": "story_id",
       "url": "故事URL",
       "publisher_id": "發布者ID",
       "og_title": "Open Graph 標題",
       "og_image": "Open Graph 圖片",
       "og_description": "Open Graph 描述",
       "full_screen_ad": False,
       "isMember": True,
       "published_date": "發布日期",
       "story_type": "故事類型"
   }
   ```

3. **發布者數據 (Publisher Data)**
   ```python
   {
       "id": "publisher_id",
       "title": "發布者標題",
       "customId": "自定義ID"
   }
   ```

## 運行測試

### 方法 1: 直接運行
```bash
python test_socialpage.py
```

### 方法 2: 使用測試運行器
```bash
python run_socialpage_tests.py
```

### 方法 3: 使用 unittest 模組
```bash
python -m unittest test_socialpage.py -v
```

### 方法 4: 包含在所有測試中
```bash
python run_all_tests.py
```

## 測試配置

### 環境變數
測試會自動設置以下環境變數：
- `MESH_GQL_ENDPOINT`: GQL 端點 URL
- `ENV`: 環境類型 (dev/prod/staging)

### Mock 對象
測試使用以下 Mock 對象：
- `pymongo.MongoClient`: 模擬 MongoDB 客戶端
- `src.gql.gql_query`: 模擬 GQL 查詢
- `src.cache.get_cache/set_cache`: 模擬緩存操作
- `fastapi_cache.FastAPICache`: 模擬 FastAPI 緩存

## 測試統計

- **總測試數量**: 13 個測試方法
- **異步測試**: 10 個
- **同步測試**: 3 個
- **測試覆蓋範圍**: 
  - 正常流程測試
  - 錯誤處理測試
  - 邊界情況測試
  - 配置測試

## 注意事項

1. **異步測試**: 大部分測試是異步的，使用 `async/await` 語法
2. **Mock 隔離**: 每個測試都使用獨立的 Mock 對象，確保測試隔離
3. **環境清理**: 測試會在 `tearDown` 中清理環境變數
4. **超時處理**: 測試設置了 300 秒的超時限制

## 維護指南

### 添加新測試
1. 在 `TestGetSocialPage` 類中添加新的測試方法
2. 使用適當的 `@patch` 裝飾器模擬依賴
3. 確保測試方法名稱以 `test_` 開頭
4. 添加詳細的文檔字符串說明測試目的

### 修改現有測試
1. 確保修改不會影響其他測試
2. 更新相關的文檔
3. 運行所有測試確保沒有回歸

### 測試數據更新
1. 如果 `getSocialPage` 函數的數據結構發生變化，需要更新相應的測試數據
2. 確保 Mock 數據與實際數據結構一致 