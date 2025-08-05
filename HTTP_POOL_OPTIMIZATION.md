# HTTP 連接池優化

## 概述

本次優化主要針對 HTTP 連接池進行改善，解決了每次 GQL 請求都建立新連接的問題，大幅提升了 `/gql` 端點的效能。

## 問題分析

### 原始問題
- 每次 `gql_query` 調用都會建立新的 `RequestsHTTPTransport` 和 `Client`
- 沒有連接重用機制
- 每次請求都需要建立 TCP 連接、SSL 握手等開銷
- 在高併發情況下效能瓶頸明顯

### 影響範圍
- `/gql` 端點（主要影響）
- `/notifications` 端點（間接影響，因為會調用 GQL）
- `/socialpage` 端點（間接影響）
- `/search` 端點（間接影響）
- `/invitation_codes` 端點（間接影響）

## 解決方案

### 1. 建立優化的 HTTP 客戶端 (`src/http_client.py`)

```python
class OptimizedHTTPClient:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
```

**主要特性：**
- 使用 `aiohttp` 替代 `requests`
- 實現連接池和會話重用
- 支援 JSON 和表單請求
- 自動連接管理

### 2. 連接池配置

```python
self._connector = aiohttp.TCPConnector(
    limit=100,              # 總連接數限制
    limit_per_host=30,      # 每個主機的連接數限制
    keepalive_timeout=30,   # 保持連接時間
    enable_cleanup_closed=True,  # 清理關閉的連接
    ttl_dns_cache=300,      # DNS 快取時間
)
```

### 3. 全域客戶端管理

```python
# 全域 HTTP 客戶端實例
_http_client: Optional[OptimizedHTTPClient] = None

async def get_http_client() -> OptimizedHTTPClient:
    """取得全域 HTTP 客戶端實例"""
    global _http_client
    if _http_client is None:
        _http_client = OptimizedHTTPClient()
    return _http_client
```

### 4. 應用生命週期管理

在 `main.py` 中：
```python
@app.on_event("startup")
async def startup():
    # ... 其他初始化 ...
    from src.http_client import get_http_client
    await get_http_client()  # 預先建立 HTTP 會話

@app.on_event("shutdown")
async def shutdown():
    from src.http_client import close_http_client
    await close_http_client()
```

## 效能改善

### 預期改善
- **連接建立時間**: 減少 80-90%
- **總響應時間**: 減少 30-50%
- **併發處理能力**: 提升 2-3 倍
- **資源使用**: 減少記憶體和 CPU 使用

### 測試方法
使用 `test_http_pool.py` 腳本進行效能測試：

```bash
python test_http_pool.py
```

## 實施細節

### 1. 檔案變更
- ✅ `src/http_client.py` (新增)
- ✅ `src/gql_optimized.py` (新增)
- ✅ `main.py` (更新啟動和關閉事件)
- ✅ `src/proxy.py` (已在使用優化客戶端)

### 2. 依賴項
- `aiohttp==3.8.1` (已在 requirements.txt 中)

### 3. 向後相容性
- 保持原有的 API 介面
- 不影響現有的功能
- 可以平滑升級

## 監控和調試

### 1. 連接池狀態
可以通過以下方式監控連接池狀態：
```python
from src.http_client import get_http_client

client = await get_http_client()
# 檢查連接器狀態
print(f"連接池大小: {client._connector.limit}")
print(f"每個主機限制: {client._connector.limit_per_host}")
```

### 2. 效能監控
使用現有的效能監控系統：
- `PerformanceMonitor` 會記錄網路請求時間
- 可以比較優化前後的差異

## 最佳實踐

### 1. 連接池大小調整
根據實際負載調整連接池參數：
```python
# 高併發環境
limit=200, limit_per_host=50

# 低併發環境
limit=50, limit_per_host=10
```

### 2. 超時設定
根據網路環境調整超時時間：
```python
timeout = aiohttp.ClientTimeout(
    total=30,    # 總超時
    connect=10,  # 連接超時
    sock_read=30 # 讀取超時
)
```

### 3. 錯誤處理
實現重試機制和錯誤處理：
```python
try:
    response = await client.post_json(url, data, headers)
except aiohttp.ClientError as e:
    # 處理網路錯誤
    logger.error(f"HTTP request failed: {e}")
    raise
```

## 下一步優化

1. **MongoDB 連接池**: 類似地優化資料庫連接
2. **JWT 快取**: 減少重複的 JWT 解碼
3. **非同步日誌**: 避免日誌記錄阻塞請求
4. **JSON 優化**: 使用更快的 JSON 處理庫

## 總結

HTTP 連接池優化是一個重要的效能改善，特別是在高併發環境下。通過重用 HTTP 連接，我們可以大幅減少網路開銷，提升整體應用效能。

這個優化為後續的效能改善奠定了基礎，並且不會影響現有的功能和使用方式。 