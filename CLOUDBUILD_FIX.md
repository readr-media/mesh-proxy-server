# Cloud Build 配置修復說明

## 問題分析

### 原始問題
在修改 `cloudbuild.yaml` 添加測試步驟後，部署時出現 `KeyError: 'PRIVATE_BUCKET_NAME'` 錯誤。

### 根本原因
我們在 `--set-env-vars` 中設置了默認的環境變數值，這些值覆蓋了原本在 Cloud Run 服務中設置的正確環境變數。

## 修復方案

### 1. 使用 update-env-vars 而不是 set-env-vars
將 `cloudbuild.yaml` 中的 `--set-env-vars` 修改為 `--update-env-vars`：

```yaml
# 修復前（會覆蓋所有原有環境變數）
--set-env-vars=ENVIRONMENT=$_ENVIRONMENT,PRIVATE_BUCKET_NAME=$_PRIVATE_BUCKET_NAME,KEYFILE_BLOB_NAME=$_KEYFILE_BLOB_NAME,MESH_GQL_ENDPOINT=$_MESH_GQL_ENDPOINT,JWT_SECRET=$_JWT_SECRET,MONGO_URL=$_MONGO_URL

# 修復後（只添加 ENVIRONMENT 變數，保留其他環境變數）
--update-env-vars=ENVIRONMENT=$_ENVIRONMENT
```

**重要區別：**
- `--set-env-vars`: 完全替換所有環境變數
- `--update-env-vars`: 只更新指定的環境變數，保留其他現有變數

### 2. 清理 substitutions
移除 `substitutions` 中不需要的環境變數定義，只保留必要的構建變數：

```yaml
substitutions:
  _PLATFORM: managed
  _SERVICE_NAME: mesh-proxy-server-dev
  _TRIGGER_ID: c466ec02-49ed-40c1-a32d-f4a40418c9d9
  _DEPLOY_REGION: asia-east1
  _AR_HOSTNAME: asia-east1-docker.pkg.dev
  _ENVIRONMENT: dev
  # 移除了以下變數，因為它們應該在 Cloud Run 服務中設置
  # _PRIVATE_BUCKET_NAME: mirrorlearning-private-bucket
  # _KEYFILE_BLOB_NAME: firebase-keyfile.json
  # _MESH_GQL_ENDPOINT: https://your-gql-endpoint.com/graphql
  # _JWT_SECRET: your-jwt-secret
  # _MONGO_URL: mongodb://your-mongo-url
```

## 為什麼原本能正常工作

### Cloud Run Source Deploy 機制
原本的配置能正常工作是因為：

1. **觸發器級別的環境變數**: 環境變數是在 Cloud Build 觸發器創建時設置的
2. **服務級別的環境變數**: Cloud Run 服務本身已經設置了正確的環境變數
3. **自動繼承**: Cloud Run Source Deploy 會自動繼承這些設置

### 我們的錯誤
當我們在 `cloudbuild.yaml` 中明確設置環境變數時，這些值會覆蓋原本的設置，導致：
- 原本正確的環境變數被覆蓋
- 使用我們設置的默認值（如 `your-gql-endpoint.com`）
- 應用程序無法找到正確的配置

## 正確的配置方式

### 1. Cloud Run 服務級別設置環境變數
```bash
# 在 Cloud Run 服務中設置環境變數
gcloud run services update mesh-proxy-server-dev \
    --region=asia-east1 \
    --set-env-vars="PRIVATE_BUCKET_NAME=your-actual-bucket,KEYFILE_BLOB_NAME=firebase-keyfile.json,MESH_GQL_ENDPOINT=https://your-actual-endpoint.com/graphql,JWT_SECRET=your-actual-secret,MONGO_URL=mongodb://your-actual-mongo-url"
```

### 2. Cloud Build 只設置構建相關變數
```yaml
# cloudbuild.yaml 只設置構建和部署相關的變數
substitutions:
  _SERVICE_NAME: mesh-proxy-server-dev
  _ENVIRONMENT: dev
  # 其他構建相關變數...
```

### 3. 觸發器級別設置（可選）
```bash
# 在觸發器中設置環境變數（如果需要）
gcloud builds triggers update github mesh-proxy-server-dev \
    --substitutions="_SERVICE_NAME=mesh-proxy-server-dev,_ENVIRONMENT=dev"
```

## 最佳實踐

### 1. 環境變數管理
- **敏感信息**: 在 Cloud Run 服務中設置
- **構建配置**: 在 `cloudbuild.yaml` 中設置
- **環境標識**: 在部署時設置（如 `ENVIRONMENT=dev`）

### 2. 配置分離
- **構建配置**: 與代碼一起版本控制
- **環境配置**: 在部署環境中管理
- **敏感配置**: 使用 Secret Manager 或環境變數

### 3. 測試和部署
- **測試階段**: 使用 Mock 或測試環境變數
- **部署階段**: 使用實際的環境變數
- **驗證階段**: 檢查服務是否正常啟動

## 驗證修復

### 1. 檢查環境變數
```bash
# 查看 Cloud Run 服務的環境變數
gcloud run services describe mesh-proxy-server-dev --region=asia-east1 --format="value(spec.template.spec.containers[0].env[].name,spec.template.spec.containers[0].env[].value)"
```

### 2. 重新部署
```bash
# 提交代碼觸發新的構建
git add .
git commit -m "Fix Cloud Build configuration - preserve existing environment variables"
git push origin dev
```

### 3. 檢查日誌
```bash
# 查看構建日誌
gcloud builds list --limit=1
gcloud builds log BUILD_ID

# 查看服務日誌
gcloud run services logs read mesh-proxy-server-dev --region=asia-east1
```

## 總結

修復的關鍵是：
1. **不要覆蓋現有的環境變數**
2. **只在必要時添加新的環境變數**
3. **保持 Cloud Run 服務的原有配置**
4. **使用正確的配置層級**

這樣既保持了測試功能，又不會破壞原有的環境配置。 