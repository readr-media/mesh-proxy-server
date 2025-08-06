# 搜尋效能優化方案

## 問題分析

根據程式碼分析，原始的搜尋實作存在以下效能瓶頸：

### 1. 順序執行搜尋
- 原始版本：`story` → `collection` → `member` → `publisher` 順序執行
- 問題：每個搜尋類型都需要等待前一個完成，總時間 = 所有搜尋時間的總和

### 2. 重複建立 MeiliSearch 連接
- 每次搜尋都建立新的 MeiliSearch 客戶端
- 問題：連接建立和銷毀的開銷

### 3. 缺乏詳細的效能監控
- 無法準確定位效能瓶頸
- 問題：難以進行針對性優化

### 4. 快取策略不夠完善
- 只有故事搜尋有快取
- 問題：其他搜尋類型無法享受快取優勢

## 優化方案

### 1. 並行搜尋處理

**實作方式：**
```python
# 建立並行任務
tasks = []
if "story" in objectives:
    tasks.append(("story", search_related_stories_optimized(search_text)))
if "collection" in objectives:
    tasks.append(("collection", search_related_collections_optimized(search_text)))
# ... 其他搜尋類型

# 並行執行
results = await asyncio.gather(*[task[1] for task in tasks])
```

**預期改善：** 總時間 ≈ 最慢的單個搜尋時間（而非總和）

### 2. 全域 MeiliSearch 客戶端

**實作方式：**
```python
_meilisearch_client: Optional[meilisearch.Client] = None

def get_meilisearch_client() -> meilisearch.Client:
    global _meilisearch_client
    if _meilisearch_client is None:
        _meilisearch_client = meilisearch.Client(MEILISEARCH_HOST, MEILISEARCH_APIKEY)
    return _meilisearch_client
```

**預期改善：** 減少連接建立開銷

### 3. 詳細效能監控

**實作方式：**
```python
async with monitor_stage(monitor, "cache_check"):
    # 快取檢查階段
async with monitor_stage(monitor, "meilisearch_search"):
    # MeiliSearch 搜尋階段
async with monitor_stage(monitor, "gql_fetch"):
    # GraphQL 查詢階段
async with monitor_stage(monitor, "post_processing"):
    # 後處理階段
```

**預期改善：** 精確定位效能瓶頸

### 4. 全面快取策略

**實作方式：**
- 為所有搜尋類型添加快取
- 使用不同的 TTL 設定
- 快取鍵包含搜尋文字和類型

**預期改善：** 重複搜尋的響應時間大幅縮短

## 效能改善預期

### 1. 並行處理改善
- **原始版本：** 4 個搜尋順序執行，總時間 = 4 × 平均搜尋時間
- **優化版本：** 4 個搜尋並行執行，總時間 ≈ 最慢搜尋時間
- **預期改善：** 60-80% 的時間縮短

### 2. 快取改善
- **首次搜尋：** 正常時間
- **重複搜尋：** 快取命中，時間縮短 90% 以上
- **預期改善：** 熱門搜尋詞的響應時間大幅改善

### 3. 連接池改善
- **原始版本：** 每次建立新連接
- **優化版本：** 重用連接
- **預期改善：** 減少 10-20% 的連接開銷

## 使用方式

### 1. 啟用優化版本

在 `main.py` 中，搜尋端點已經更新為使用優化版本：

```python
@app.post('/search')
async def search_post(search: Search):
    # 使用優化的搜尋函數
    from src.search_optimized import search_all_optimized
    related_data = await search_all_optimized(search_text, objectives, monitor=monitor)
```

### 2. 效能監控

優化版本包含詳細的效能監控，可以通過以下方式查看：

```python
# 在搜尋函數中
monitor = PerformanceMonitor("POST: /search")
monitor.start()
# ... 執行搜尋
monitor.end()
await log_performance_detailed_async(monitor)
```

### 3. 測試效能改善

執行測試腳本來比較效能：

```bash
python test_search_optimization.py
```

## 配置選項

### 快取 TTL 設定

在 `src/config.py` 中可以調整快取時間：

```python
SEARCH_STORY_CACHE_TTL = 3600      # 故事搜尋快取 1 小時
SEARCH_COLLECTION_CACHE_TTL = 300  # 集合搜尋快取 5 分鐘
SEARCH_MEMBER_CACHE_TTL = 300      # 成員搜尋快取 5 分鐘
SEARCH_PUBLISHER_CACHE_TTL = 3600  # 發布者搜尋快取 1 小時
```

### 搜尋結果數量

```python
MEILISEARCH_RELATED_STORIES_NUM = 10
MEILISEARCH_RELATED_COLLECTIONS_NUM = 5
MEILISEARCH_RELATED_MEMBER_NUM = 10
MEILISEARCH_RELATED_PUBLISHERS_NUM = 3
```

## 監控和診斷

### 1. 效能日誌

優化版本會記錄詳細的效能資訊，包括：
- 各階段的執行時間
- 快取命中率
- 並行處理效果

### 2. 錯誤處理

包含完善的錯誤處理和診斷資訊：
- 搜尋失敗時提供詳細錯誤訊息
- 自動診斷系統狀態
- 提供修復建議

### 3. 健康檢查

可以通過 `/diagnostic` 端點檢查系統狀態：
- MeiliSearch 連接狀態
- Redis 快取狀態
- GraphQL 端點狀態

## 最佳實踐建議

### 1. 快取策略
- 根據搜尋頻率調整 TTL
- 熱門搜尋詞使用較長的快取時間
- 冷門搜尋詞使用較短的快取時間

### 2. 並行處理
- 根據系統資源調整並行數量
- 監控並行處理的效能影響
- 避免過度並行導致資源競爭

### 3. 監控和警報
- 設定效能閾值警報
- 監控快取命中率
- 追蹤搜尋響應時間趨勢

## 總結

通過以上優化方案，預期可以實現：

1. **響應時間改善：** 60-80% 的整體改善
2. **快取效果：** 重複搜尋 90% 以上的時間縮短
3. **系統穩定性：** 更好的錯誤處理和診斷能力
4. **可觀測性：** 詳細的效能監控和日誌

這些改善將顯著提升用戶體驗，特別是在高併發場景下的搜尋效能。 