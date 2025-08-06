# 環境變數配置說明

## 概述

Cloud Build 配置中需要設置多個環境變數以確保應用程序正常運行。以下是所有必需的環境變數及其說明。

## 必需的環境變數

### 1. Firebase 相關
- **`PRIVATE_BUCKET_NAME`**: Google Cloud Storage 私有存儲桶名稱
  - 用於存儲 Firebase 服務賬戶密鑰文件
  - 示例: `mirrorlearning-private-bucket`

- **`KEYFILE_BLOB_NAME`**: Firebase 密鑰文件在存儲桶中的路徑
  - 示例: `firebase-keyfile.json`

### 2. GraphQL 相關
- **`MESH_GQL_ENDPOINT`**: GraphQL API 端點
  - 示例: `https://your-gql-endpoint.com/graphql`

### 3. JWT 相關
- **`JWT_SECRET`**: JWT 令牌簽名密鑰
  - 用於生成和驗證 JWT 令牌
  - 示例: `your-jwt-secret-key`

### 4. 數據庫相關
- **`MONGO_URL`**: MongoDB 連接字符串
  - 示例: `mongodb://username:password@host:port/database`

### 5. 其他
- **`ENVIRONMENT`**: 環境名稱（自動設置）
  - dev 環境: `dev`
  - prod 環境: `prod`

## 設置方法

### 方法 1: 在 Cloud Build 觸發器中設置

創建觸發器時指定環境變數：

```bash
# Dev 環境觸發器
gcloud builds triggers create github \
    --name="mesh-proxy-server-dev" \
    --repo-name="mesh-proxy-server" \
    --repo-owner="hcchien" \
    --branch-pattern="^dev$" \
    --build-config="cloudbuild.yaml" \
    --substitutions="_SERVICE_NAME=mesh-proxy-server-dev,_ENVIRONMENT=dev,_PRIVATE_BUCKET_NAME=your-dev-bucket,_KEYFILE_BLOB_NAME=firebase-keyfile.json,_MESH_GQL_ENDPOINT=https://dev-gql-endpoint.com/graphql,_JWT_SECRET=your-dev-jwt-secret,_MONGO_URL=mongodb://dev-mongo-url" \
    --description="Dev environment trigger for mesh-proxy-server"

# Prod 環境觸發器
gcloud builds triggers create github \
    --name="mesh-proxy-server-prod" \
    --repo-name="mesh-proxy-server" \
    --repo-owner="hcchien" \
    --branch-pattern="^prod$" \
    --build-config="cloudbuild-prod.yaml" \
    --substitutions="_SERVICE_NAME=mesh-proxy-server-prod,_ENVIRONMENT=prod,_PRIVATE_BUCKET_NAME=your-prod-bucket,_KEYFILE_BLOB_NAME=firebase-keyfile.json,_MESH_GQL_ENDPOINT=https://prod-gql-endpoint.com/graphql,_JWT_SECRET=your-prod-jwt-secret,_MONGO_URL=mongodb://prod-mongo-url" \
    --description="Production environment trigger for mesh-proxy-server"
```

### 方法 2: 在 Cloud Run 服務中設置

直接在 Cloud Run 服務中設置環境變數：

```bash
# 設置 dev 環境變數
gcloud run services update mesh-proxy-server-dev \
    --region=asia-east1 \
    --set-env-vars="PRIVATE_BUCKET_NAME=your-dev-bucket,KEYFILE_BLOB_NAME=firebase-keyfile.json,MESH_GQL_ENDPOINT=https://dev-gql-endpoint.com/graphql,JWT_SECRET=your-dev-jwt-secret,MONGO_URL=mongodb://dev-mongo-url"

# 設置 prod 環境變數
gcloud run services update mesh-proxy-server-prod \
    --region=asia-east1 \
    --set-env-vars="PRIVATE_BUCKET_NAME=your-prod-bucket,KEYFILE_BLOB_NAME=firebase-keyfile.json,MESH_GQL_ENDPOINT=https://prod-gql-endpoint.com/graphql,JWT_SECRET=your-prod-jwt-secret,MONGO_URL=mongodb://prod-mongo-url"
```

## 安全考慮

### 敏感信息處理
- **JWT_SECRET**: 使用強密碼，不同環境使用不同的密鑰
- **MongoDB 密碼**: 使用環境變數而不是硬編碼
- **Firebase 密鑰**: 存儲在私有存儲桶中

### 權限設置
確保 Cloud Run 服務賬戶有權限：
- 讀取 Google Cloud Storage 中的 Firebase 密鑰文件
- 訪問 MongoDB 數據庫
- 調用 GraphQL API

## 故障排除

### 常見錯誤

1. **KeyError: 'PRIVATE_BUCKET_NAME'**
   - 檢查環境變數是否正確設置
   - 確認 Cloud Run 服務中的環境變數

2. **Firebase 初始化失敗**
   - 檢查 Firebase 密鑰文件是否存在
   - 確認存儲桶權限設置

3. **MongoDB 連接失敗**
   - 檢查 MongoDB URL 格式
   - 確認網絡連接和認證信息

### 檢查環境變數

```bash
# 查看 Cloud Run 服務的環境變數
gcloud run services describe mesh-proxy-server-dev --region=asia-east1 --format="value(spec.template.spec.containers[0].env[].name,spec.template.spec.containers[0].env[].value)"
```

## 最佳實踐

1. **環境分離**: 不同環境使用不同的配置
2. **密鑰輪換**: 定期更新 JWT 密鑰和數據庫密碼
3. **監控**: 設置日誌監控來檢測配置問題
4. **備份**: 定期備份環境變數配置
5. **文檔**: 保持環境變數文檔的更新 