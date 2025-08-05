# 效能診斷指南

## 問題描述

你的 `/gql` endpoint 在 nginx 日誌中顯示回應時間超過 1.x 秒，但程式內部的 `execute_time` 看起來不長。這表示瓶頸可能出現在：

1. **Google Cloud Logging 的同步呼叫**
2. **JWT 解碼和 ACL 檢查**
3. **網路延遲**
4. **FastAPI 的請求處理**

## 解決方案

### 1. 詳細效能監控

我已經為你建立了一個詳細的效能監控系統，會追蹤以下階段：

- `acl_check`: ACL 檢查階段
- `jwt_decoding`: JWT 解碼階段  
- `acl_processing`: ACL 處理階段
- `gql_proxy`: GQL 代理階段
  - `request_preparation`: 請求準備
  - `network_request`: 網路請求
  - `response_processing`: 回應處理
- `response_handling`: 回應處理階段

### 2. 非同步日誌記錄

將原本的同步 Google Cloud Logging 改為非同步，避免阻塞主執行緒。

### 3. 診斷工具

提供了一個效能診斷工具來測試你的 endpoint。

## 使用方法

### 1. 部署更新

將更新的程式碼部署到你的環境中。

### 2. 查看詳細日誌

現在你的效能日誌會包含詳細的階段分析：

```json
{
  "endpoint": "POST: /gql",
  "total_duration": 1.234,
  "stages": {
    "acl_check": {
      "duration": 0.001,
      "metadata": {}
    },
    "jwt_decoding": {
      "duration": 0.002,
      "metadata": {}
    },
    "acl_processing": {
      "duration": 0.003,
      "metadata": {}
    },
    "gql_proxy": {
      "duration": 1.200,
      "metadata": {}
    },
    "request_preparation": {
      "duration": 0.001,
      "metadata": {}
    },
    "network_request": {
      "duration": 1.180,
      "metadata": {}
    },
    "response_processing": {
      "duration": 0.019,
      "metadata": {}
    },
    "response_handling": {
      "duration": 0.028,
      "metadata": {}
    }
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

### 3. 使用診斷工具

```bash
# 安裝依賴
pip install aiohttp

# 執行診斷測試
python diagnostic_tools.py \
  --url "https://your-api-domain.com" \
  --token "your-jwt-token" \
  --query "query { stories { id title } }" \
  --requests 20
```

### 4. 分析 nginx 日誌

檢查 nginx 日誌中的時間戳記，對比程式內部的效能日誌：

```bash
# 查看 nginx 日誌
tail -f /var/log/nginx/access.log | grep "/gql"

# 查看應用程式日誌
tail -f /var/log/your-app.log | grep "PERFORMANCE MONITOR"
```

## 常見瓶頸分析

### 1. 如果 `network_request` 時間很長
- 檢查 GQL server 的網路延遲
- 考慮使用連接池
- 檢查 DNS 解析時間

### 2. 如果 `jwt_decoding` 或 `acl_processing` 時間很長
- 檢查 JWT token 的大小
- 優化 ACL 檢查邏輯
- 考慮快取 ACL 結果

### 3. 如果 `response_handling` 時間很長
- 檢查回應大小
- 優化 JSON 序列化
- 檢查記憶體使用

### 4. 如果總時間與 nginx 時間差異很大
- 檢查 FastAPI 的 middleware
- 檢查 nginx 的 proxy 設定
- 檢查 SSL/TLS 握手時間

## 進一步優化建議

### 1. 連接池優化
```python
# 在 proxy.py 中使用連接池
import aiohttp

# 建立全域連接池
session = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(
        limit=100,
        limit_per_host=30,
        ttl_dns_cache=300
    )
)
```

### 2. ACL 快取
```python
# 快取 ACL 檢查結果
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_acl_check(token_hash: str):
    # ACL 檢查邏輯
    pass
```

### 3. 回應壓縮
```python
# 在 FastAPI 中啟用回應壓縮
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## 監控建議

1. **設定警報**：當回應時間超過閾值時發送通知
2. **定期報告**：每小時/每天生成效能報告
3. **趨勢分析**：追蹤效能變化趨勢
4. **容量規劃**：根據效能數據規劃擴展

## 故障排除

如果遇到問題：

1. 檢查環境變數設定
2. 確認 Google Cloud Logging 權限
3. 檢查網路連接
4. 查看應用程式錯誤日誌

## 聯絡支援

如果問題持續存在，請提供：
- 詳細的效能日誌
- nginx 日誌片段
- 診斷工具的輸出結果
- 系統資源使用情況 