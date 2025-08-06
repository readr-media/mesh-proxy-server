# 多環境 Cloud Build 設置說明

## 概述

我們已經為您的項目設置了支持多環境（dev 和 prod）的 Cloud Build 配置，包含完整的測試流程。

## 文件結構

```
├── cloudbuild.yaml          # dev 環境配置
├── cloudbuild-prod.yaml     # prod 環境配置
├── setup_triggers.sh        # 觸發器設置腳本
├── run_all_tests.py         # 測試腳本
└── .cloudbuildignore        # 構建忽略文件
```

## 環境配置

### Dev 環境 (cloudbuild.yaml)
- **服務名稱**: `mesh-proxy-server-dev`
- **觸發分支**: `dev`
- **環境變數**: `ENVIRONMENT=dev`
- **標籤**: `environment=dev`

### Prod 環境 (cloudbuild-prod.yaml)
- **服務名稱**: `mesh-proxy-server-prod`
- **觸發分支**: `prod`
- **環境變數**: `ENVIRONMENT=prod`
- **標籤**: `environment=prod`

## 構建流程

每個環境的構建都包含以下步驟：

1. **安裝依賴並運行測試**
   - 安裝 Python 依賴
   - 運行所有單元測試
   - 只有測試通過才會繼續

2. **構建 Docker 鏡像**
   - 使用 Dockerfile 構建鏡像
   - 推送到 Container Registry

3. **部署到 Cloud Run**
   - 更新 Cloud Run 服務
   - 設置環境變數和標籤

## 設置觸發器

### 自動設置
運行設置腳本：
```bash
chmod +x setup_triggers.sh
./setup_triggers.sh
```

### 手動設置

#### Dev 環境觸發器
```bash
gcloud builds triggers create github \
    --name="mesh-proxy-server-dev" \
    --repo-name="mesh-proxy-server" \
    --repo-owner="hcchien" \
    --branch-pattern="^dev$" \
    --build-config="cloudbuild.yaml" \
    --substitutions="_SERVICE_NAME=mesh-proxy-server-dev,_ENVIRONMENT=dev" \
    --description="Dev environment trigger for mesh-proxy-server"
```

#### Prod 環境觸發器
```bash
gcloud builds triggers create github \
    --name="mesh-proxy-server-prod" \
    --repo-name="mesh-proxy-server" \
    --repo-owner="hcchien" \
    --branch-pattern="^prod$" \
    --build-config="cloudbuild-prod.yaml" \
    --substitutions="_SERVICE_NAME=mesh-proxy-server-prod,_ENVIRONMENT=prod" \
    --description="Production environment trigger for mesh-proxy-server"
```

## 工作流程

### 開發流程
1. 在 `dev` 分支進行開發
2. 提交代碼到 `dev` 分支
3. 自動觸發 dev 環境構建
4. 運行測試，如果通過則部署到 dev 環境

### 生產部署流程
1. 將 `dev` 分支合併到 `prod` 分支
2. 提交到 `prod` 分支
3. 自動觸發 prod 環境構建
4. 運行測試，如果通過則部署到 prod 環境

## 測試覆蓋

每個構建都會運行以下測試：
- 依賴檢查
- 代碼風格檢查
- 單元測試（包括 notify.py 的 11 個測試案例）
- 其他現有測試

## 環境變數

### 自動設置的環境變數
- `ENVIRONMENT`: 環境名稱（dev 或 prod）

### 需要手動設置的環境變數
在 Cloud Run 服務中設置：
- `MESH_GQL_ENDPOINT`: GraphQL 端點
- `MONGO_URL`: MongoDB 連接字符串
- 其他業務相關的環境變數

## 監控和日誌

### 查看構建日誌
```bash
# 查看最近的構建
gcloud builds list --limit=10

# 查看特定構建的日誌
gcloud builds log BUILD_ID
```

### 查看 Cloud Run 服務
```bash
# 查看 dev 環境
gcloud run services describe mesh-proxy-server-dev --region=asia-east1

# 查看 prod 環境
gcloud run services describe mesh-proxy-server-prod --region=asia-east1
```

## 故障排除

### 常見問題

1. **觸發器不工作**
   - 檢查分支名稱是否正確
   - 確認 GitHub 連接設置
   - 查看觸發器日誌

2. **測試失敗**
   - 檢查依賴是否正確安裝
   - 查看測試輸出日誌
   - 確認測試數據結構

3. **部署失敗**
   - 檢查 Cloud Run 服務是否存在
   - 確認權限設置
   - 查看部署日誌

### 手動觸發構建
```bash
# dev 環境
gcloud builds submit --config=cloudbuild.yaml --substitutions=_SERVICE_NAME=mesh-proxy-server-dev,_ENVIRONMENT=dev

# prod 環境
gcloud builds submit --config=cloudbuild-prod.yaml --substitutions=_SERVICE_NAME=mesh-proxy-server-prod,_ENVIRONMENT=prod
```

## 最佳實踐

1. **分支管理**
   - 使用 `dev` 分支進行開發
   - 使用 `prod` 分支進行生產部署
   - 通過 Pull Request 進行代碼審查

2. **測試策略**
   - 在 dev 環境充分測試
   - 確保所有測試通過後再部署到 prod
   - 定期檢查測試覆蓋率

3. **部署策略**
   - 使用藍綠部署或滾動更新
   - 設置健康檢查
   - 監控服務性能

4. **安全考慮**
   - 使用最小權限原則
   - 定期更新依賴
   - 監控安全日誌 