# MongoDB 連接池優化

## 概述

本次優化主要針對 MongoDB 連接池進行改善，解決了每次資料庫操作都建立新連接的問題，大幅提升了 `/notifications` 和 `/socialpage` 端點的效能。

## 問題分析

### 原始問題
- 每次 `connect_db` 調用都會建立新的 `pymongo.MongoClient`
- 沒有連接重用機制
- 每次查詢都需要建立 TCP 連接、認證等開銷
- 在高併發情況下資料庫連接成為瓶頸
- 同步操作阻塞事件循環

### 影響範圍
- `/notifications` 端點（主要影響）
- `/socialpage` 端點（主要影響）
- 所有使用 MongoDB 的端點（間接影響）

## 解決方案

### 1. 建立 MongoDB 連接管理器 (`src/mongo_client.py`)

```python
class MongoManager:
    def __init__(self):
        self._async_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self._sync_client: Optional[pymongo.MongoClient] = None
```

**主要特性：**
- 使用 `motor` 實現非同步 MongoDB 操作
- 實現連接池和會話重用
- 支援同步和非同步兩種模式
- 自動連接管理

### 2. 連接池配置

```python
self._async_client = motor.motor_asyncio.AsyncIOMotorClient(
    mongo_url,
    maxPoolSize=50,              # 連接池大小
    minPoolSize=10,              # 最小連接數
    maxIdleTimeMS=30000,         # 最大空閒時間
    waitQueueTimeoutMS=5000,     # 等待隊列超時
    serverSelectionTimeoutMS=5000, # 服務器選擇超時
    connectTimeoutMS=10000,      # 連接超時
    socketTimeoutMS=30000,       # Socket 超時
)
```

### 3. 全域管理器管理

```python
# 全域 MongoDB 管理器實例
_mongo_manager: Optional[MongoManager] = None

async def get_mongo_manager() -> MongoManager:
    """取得全域 MongoDB 管理器實例"""
    global _mongo_manager
    if _mongo_manager is None:
        _mongo_manager = MongoManager()
    return _mongo_manager
```

### 4. 應用生命週期管理

在 `main.py` 中：
```python
@app.on_event("startup")
async def startup():
    # ... 其他初始化 ...
    from src.mongo_client import initialize_mongo
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    env = os.environ.get('ENV', 'dev')
    await initialize_mongo(mongo_url, env)

@app.on_event("shutdown")
async def shutdown():
    # ... 其他清理 ...
    from src.mongo_client import close_mongo
    await close_mongo()
```

### 5. 優化的通知函數 (`src/notify_optimized.py`)

```python
async def get_notifies_optimized(memberId: str, index: int = 0, take: int = 10):
    # 使用 MongoDB 連接池
    mongo_manager = await get_mongo_manager()
    db = mongo_manager.get_async_db()
    col_notify = db.notifications
    
    # 使用非同步查詢
    record = await col_notify.find_one({"_id": memberId})
```

### 6. 優化的社交頁面函數 (`src/socialpage_optimized.py`)

```python
async def getSocialPage_optimized(member_id: str, index: int = 0, take: int = 0):
    # 使用 MongoDB 連接池
    mongo_manager = await get_mongo_manager()
    db = mongo_manager.get_async_db()
    col_members, col_stories = db.members, db.stories
    
    # 使用非同步查詢
    member_info = await col_members.find_one({"_id": member_id})
```

## 效能改善

### 預期改善
- **連接建立時間**: 減少 80-90%
- **總響應時間**: 減少 40-60%
- **併發處理能力**: 提升 3-5 倍
- **資源使用**: 減少記憶體和 CPU 使用
- **事件循環阻塞**: 完全消除

### 測試方法
使用 `test_mongo_pool.py` 腳本進行效能測試：

```bash
python test_mongo_pool.py
```

## 實施細節

### 1. 檔案變更
- ✅ `src/mongo_client.py` (新增)
- ✅ `src/notify_optimized.py` (新增)
- ✅ `src/socialpage_optimized.py` (新增)
- ✅ `main.py` (更新啟動和關閉事件)
- ✅ `requirements.txt` (添加 motor 依賴)

### 2. 依賴項
- `motor==3.3.2` (新增)
- `pymongo==4.8.0` (已存在)

### 3. 向後相容性
- 保持原有的 API 介面
- 提供同步和非同步兩種模式
- 不影響現有的功能
- 可以平滑升級

## 監控和調試

### 1. 連接池狀態
可以通過以下方式監控連接池狀態：
```python
from src.mongo_client import get_mongo_manager

manager = await get_mongo_manager()
async_client = manager.get_async_client()
print(f"連接池大小: {async_client.options.max_pool_size}")
print(f"最小連接數: {async_client.options.min_pool_size}")
```

### 2. 效能監控
使用現有的效能監控系統：
- `PerformanceMonitor` 會記錄資料庫操作時間
- 可以比較優化前後的差異

## 最佳實踐

### 1. 連接池大小調整
根據實際負載調整連接池參數：
```python
# 高併發環境
maxPoolSize=100, minPoolSize=20

# 低併發環境
maxPoolSize=20, minPoolSize=5
```

### 2. 超時設定
根據網路環境調整超時時間：
```python
connectTimeoutMS=10000,    # 連接超時
socketTimeoutMS=30000,     # Socket 超時
serverSelectionTimeoutMS=5000,  # 服務器選擇超時
```

### 3. 錯誤處理
實現重試機制和錯誤處理：
```python
try:
    result = await collection.find_one(query)
except motor.errors.ServerSelectionTimeoutError:
    # 處理服務器選擇超時
    logger.error("MongoDB server selection timeout")
    raise
except motor.errors.ConnectionFailure:
    # 處理連接失敗
    logger.error("MongoDB connection failed")
    raise
```

## 非同步操作優勢

### 1. 事件循環友好
- 非同步操作不會阻塞事件循環
- 可以同時處理多個資料庫請求
- 提升整體應用響應性

### 2. 連接重用
- 連接在請求之間保持活躍
- 減少連接建立和認證開銷
- 提升查詢效能

### 3. 資源管理
- 自動管理連接生命週期
- 防止連接洩漏
- 優化記憶體使用

## 下一步優化

1. **JWT 快取**: 減少重複的 JWT 解碼
2. **非同步日誌**: 避免日誌記錄阻塞請求
3. **JSON 優化**: 使用更快的 JSON 處理庫
4. **快取策略優化**: 為更多端點加入智慧快取

## 總結

MongoDB 連接池優化是一個重要的效能改善，特別是在高併發環境下。通過重用資料庫連接和使用非同步操作，我們可以大幅減少資料庫開銷，提升整體應用效能。

這個優化與 HTTP 連接池優化相輔相成，為應用提供了完整的連接池解決方案。 