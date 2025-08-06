#!/bin/bash

# Cloud Build 觸發器設置腳本
# 用於創建 dev 和 prod 環境的觸發器

set -e

echo "🚀 Cloud Build 觸發器設置腳本"
echo "================================"

# 獲取項目 ID
PROJECT_ID=$(gcloud config get-value project)
echo "📋 當前項目: $PROJECT_ID"

# 獲取 GitHub 連接
echo ""
echo "🔗 檢查 GitHub 連接..."
GITHUB_CONNECTION=$(gcloud builds triggers list --filter='github.name:*' --format='value(github.name)' | head -1)

if [ -z "$GITHUB_CONNECTION" ]; then
    echo "❌ 沒有找到 GitHub 連接"
    echo "請先創建 GitHub 連接:"
    echo "gcloud builds triggers create-github-connection --name=github-connection --repository=YOUR_GITHUB_REPO"
    exit 1
fi

echo "✅ 找到 GitHub 連接: $GITHUB_CONNECTION"

# 創建 dev 環境觸發器
echo ""
echo "🔧 創建 dev 環境觸發器..."
DEV_TRIGGER_NAME="mesh-proxy-server-dev"
DEV_SERVICE_NAME="mesh-proxy-server-dev"

# 檢查是否已存在
if gcloud builds triggers list --filter="name=$DEV_TRIGGER_NAME" --format="value(name)" | grep -q "$DEV_TRIGGER_NAME"; then
    echo "⚠️  dev 觸發器已存在，刪除舊的..."
    gcloud builds triggers delete "$DEV_TRIGGER_NAME" --quiet
fi

# 創建新的 dev 觸發器
gcloud builds triggers create github \
    --name="$DEV_TRIGGER_NAME" \
    --repo-name="mesh-proxy-server" \
    --repo-owner="hcchien" \
    --branch-pattern="^dev$" \
    --build-config="cloudbuild.yaml" \
    --substitutions="_SERVICE_NAME=$DEV_SERVICE_NAME,_ENVIRONMENT=dev" \
    --description="Dev environment trigger for mesh-proxy-server"

echo "✅ dev 觸發器創建成功"

# 創建 prod 環境觸發器
echo ""
echo "🔧 創建 prod 環境觸發器..."
PROD_TRIGGER_NAME="mesh-proxy-server-prod"
PROD_SERVICE_NAME="mesh-proxy-server-prod"

# 檢查是否已存在
if gcloud builds triggers list --filter="name=$PROD_TRIGGER_NAME" --format="value(name)" | grep -q "$PROD_TRIGGER_NAME"; then
    echo "⚠️  prod 觸發器已存在，刪除舊的..."
    gcloud builds triggers delete "$PROD_TRIGGER_NAME" --quiet
fi

# 創建新的 prod 觸發器
gcloud builds triggers create github \
    --name="$PROD_TRIGGER_NAME" \
    --repo-name="mesh-proxy-server" \
    --repo-owner="hcchien" \
    --branch-pattern="^prod$" \
    --build-config="cloudbuild-prod.yaml" \
    --substitutions="_SERVICE_NAME=$PROD_SERVICE_NAME,_ENVIRONMENT=prod" \
    --description="Production environment trigger for mesh-proxy-server"

echo "✅ prod 觸發器創建成功"

# 顯示所有觸發器
echo ""
echo "📋 所有觸發器列表:"
gcloud builds triggers list --format="table(name,description,github.push.branch,filename)"

echo ""
echo "🎉 觸發器設置完成！"
echo ""
echo "📝 使用說明:"
echo "  - dev 分支的提交會觸發 dev 環境部署"
echo "  - prod 分支的提交會觸發 prod 環境部署"
echo "  - 兩個環境都會運行測試，只有測試通過才會部署"
echo ""
echo "🔍 查看觸發器詳情:"
echo "  gcloud builds triggers describe $DEV_TRIGGER_NAME"
echo "  gcloud builds triggers describe $PROD_TRIGGER_NAME" 