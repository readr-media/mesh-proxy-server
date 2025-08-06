# 環境變數修復詳細說明

## 問題根源

### 關鍵問題
使用 `--set-env-vars` 會**完全替換**所有環境變數，而不是追加或更新。

### 具體影響
當我們在 `cloudbuild.yaml` 中使用：
```yaml
--set-env-vars=ENVIRONMENT=$_ENVIRONMENT
```

這會導致：
1. **清空所有現有環境變數**（包括 `PRIVATE_BUCKET_NAME`, `MESH_GQL_ENDPOINT` 等）
2. **只保留 `ENVIRONMENT` 變數**
3. **應用程序啟動失敗**，因為找不到必需的環境變數

## 解決方案

### 使用 `--update-env-vars` 而不是 `--set-env-vars`

```yaml
# ❌ 錯誤的方式（會清空所有環境變數）
--set-env-vars=ENVIRONMENT=$_ENVIRONMENT

# ✅ 正確的方式（只添加/更新指定變數）
--update-env-vars=ENVIRONMENT=$_ENVIRONMENT
```

### 參數區別

| 參數 | 行為 | 影響 |
|------|------|------|
| `--set-env-vars` | 完全替換所有環境變數 | 清空現有變數，只設置指定的變數 |
| `--update-env-vars` | 只更新指定的環境變數 | 保留現有變數，只添加/更新指定的變數 |

## 實際測試

### 測試場景
假設 Cloud Run 服務原本有以下環境變數：
- `PRIVATE_BUCKET_NAME=my-bucket`
- `MESH_GQL_ENDPOINT=https://api.example.com`
- `JWT_SECRET=my-secret`

### 使用 `--set-env-vars=ENVIRONMENT=dev`
**結果：**
- `ENVIRONMENT=dev` ✅
- `PRIVATE_BUCKET_NAME` ❌ (被清空)
- `MESH_GQL_ENDPOINT` ❌ (被清空)
- `JWT_SECRET` ❌ (被清空)

### 使用 `--update-env-vars=ENVIRONMENT=dev`
**結果：**
- `ENVIRONMENT=dev` ✅ (新增)
- `PRIVATE_BUCKET_NAME=my-bucket` ✅ (保留)
- `MESH_GQL_ENDPOINT=https://api.example.com` ✅ (保留)
- `JWT_SECRET=my-secret` ✅ (保留)

## 驗證修復

### 1. 檢查當前配置
```bash
# 查看修復後的 cloudbuild.yaml
grep -n "update-env-vars" cloudbuild.yaml
```

### 2. 檢查 Cloud Run 服務環境變數
```bash
# 部署前檢查
gcloud run services describe mesh-proxy-server-dev --region=asia-east1 --format="value(spec.template.spec.containers[0].env[].name,spec.template.spec.containers[0].env[].value)"

# 部署後檢查
gcloud run services describe mesh-proxy-server-dev --region=asia-east1 --format="value(spec.template.spec.containers[0].env[].name,spec.template.spec.containers[0].env[].value)"
```

### 3. 檢查服務日誌
```bash
# 查看服務啟動日誌
gcloud run services logs read mesh-proxy-server-dev --region=asia-east1 --limit=50
```

## 最佳實踐

### 1. 環境變數管理策略
- **構建時變數**: 使用 `--update-env-vars` 添加構建相關變數
- **業務變數**: 在 Cloud Run 服務中直接設置
- **敏感變數**: 使用 Secret Manager 或環境變數

### 2. 部署流程
```yaml
# 正確的部署步驟
steps:
  # 測試步驟
  - name: python:3.9
    # ... 測試代碼
  
  # 構建步驟
  - name: gcr.io/cloud-builders/docker
    # ... 構建代碼
  
  # 部署步驟 - 只更新必要的變數
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
    args:
      - run
      - services
      - update
      - $_SERVICE_NAME
      - '--platform=managed'
      - '--image=...'
      - '--update-env-vars=ENVIRONMENT=$_ENVIRONMENT'  # 只更新環境標識
```

### 3. 監控和驗證
- **部署前**: 檢查現有環境變數
- **部署後**: 驗證環境變數是否正確保留
- **運行時**: 監控應用程序啟動日誌

## 常見錯誤

### 1. 使用 `--set-env-vars` 清空環境變數
```yaml
# ❌ 錯誤
--set-env-vars=ENVIRONMENT=dev
```

### 2. 在 substitutions 中設置業務變數
```yaml
# ❌ 錯誤
substitutions:
  _PRIVATE_BUCKET_NAME: my-bucket  # 不應該在這裡設置
```

### 3. 忘記檢查現有配置
```bash
# ✅ 正確 - 部署前檢查
gcloud run services describe SERVICE_NAME --region=REGION
```

## 總結

修復的關鍵是理解 `--set-env-vars` 和 `--update-env-vars` 的區別：

- **`--set-env-vars`**: 完全替換，會清空所有現有環境變數
- **`--update-env-vars`**: 增量更新，只修改指定的環境變數

使用 `--update-env-vars` 可以確保：
1. 保留所有現有的環境變數
2. 只添加/更新必要的變數
3. 不會破壞應用程序的配置
4. 保持部署的穩定性和可靠性 