#!/bin/bash

# 快速修復環境變數腳本
# 用於設置 Cloud Run 服務的環境變數

set -e

echo "🔧 快速修復環境變數"
echo "=================="

# 獲取項目 ID
PROJECT_ID=$(gcloud config get-value project)
echo "📋 當前項目: $PROJECT_ID"

# 檢查 dev 服務是否存在
echo ""
echo "🔍 檢查 Cloud Run 服務..."

if gcloud run services describe mesh-proxy-server-dev --region=asia-east1 --quiet 2>/dev/null; then
    echo "✅ 找到 dev 服務"
    
    echo ""
    echo "🔧 設置 dev 環境變數..."
    
    # 請用戶輸入實際的環境變數值
    echo "請輸入以下環境變數的值（按 Enter 使用默認值）:"
    
    read -p "PRIVATE_BUCKET_NAME (默認: mirrorlearning-private-bucket): " PRIVATE_BUCKET_NAME
    PRIVATE_BUCKET_NAME=${PRIVATE_BUCKET_NAME:-mirrorlearning-private-bucket}
    
    read -p "KEYFILE_BLOB_NAME (默認: firebase-keyfile.json): " KEYFILE_BLOB_NAME
    KEYFILE_BLOB_NAME=${KEYFILE_BLOB_NAME:-firebase-keyfile.json}
    
    read -p "MESH_GQL_ENDPOINT (默認: https://dev-gql-endpoint.com/graphql): " MESH_GQL_ENDPOINT
    MESH_GQL_ENDPOINT=${MESH_GQL_ENDPOINT:-https://dev-gql-endpoint.com/graphql}
    
    read -p "JWT_SECRET (默認: your-dev-jwt-secret): " JWT_SECRET
    JWT_SECRET=${JWT_SECRET:-your-dev-jwt-secret}
    
    read -p "MONGO_URL (默認: mongodb://dev-mongo-url): " MONGO_URL
    MONGO_URL=${MONGO_URL:-mongodb://dev-mongo-url}
    
    # 設置環境變數
    echo ""
    echo "🚀 更新 dev 服務環境變數..."
    
    gcloud run services update mesh-proxy-server-dev \
        --region=asia-east1 \
        --set-env-vars="ENVIRONMENT=dev,PRIVATE_BUCKET_NAME=$PRIVATE_BUCKET_NAME,KEYFILE_BLOB_NAME=$KEYFILE_BLOB_NAME,MESH_GQL_ENDPOINT=$MESH_GQL_ENDPOINT,JWT_SECRET=$JWT_SECRET,MONGO_URL=$MONGO_URL" \
        --quiet
    
    echo "✅ dev 服務環境變數設置完成"
    
else
    echo "❌ 未找到 dev 服務"
    echo "請先部署服務或檢查服務名稱"
fi

# 檢查 prod 服務是否存在
if gcloud run services describe mesh-proxy-server-prod --region=asia-east1 --quiet 2>/dev/null; then
    echo ""
    echo "✅ 找到 prod 服務"
    
    echo ""
    echo "🔧 設置 prod 環境變數..."
    
    # 請用戶輸入實際的環境變數值
    echo "請輸入以下環境變數的值（按 Enter 使用默認值）:"
    
    read -p "PRIVATE_BUCKET_NAME (默認: mirrorlearning-private-bucket): " PRIVATE_BUCKET_NAME_PROD
    PRIVATE_BUCKET_NAME_PROD=${PRIVATE_BUCKET_NAME_PROD:-mirrorlearning-private-bucket}
    
    read -p "KEYFILE_BLOB_NAME (默認: firebase-keyfile.json): " KEYFILE_BLOB_NAME_PROD
    KEYFILE_BLOB_NAME_PROD=${KEYFILE_BLOB_NAME_PROD:-firebase-keyfile.json}
    
    read -p "MESH_GQL_ENDPOINT (默認: https://prod-gql-endpoint.com/graphql): " MESH_GQL_ENDPOINT_PROD
    MESH_GQL_ENDPOINT_PROD=${MESH_GQL_ENDPOINT_PROD:-https://prod-gql-endpoint.com/graphql}
    
    read -p "JWT_SECRET (默認: your-prod-jwt-secret): " JWT_SECRET_PROD
    JWT_SECRET_PROD=${JWT_SECRET_PROD:-your-prod-jwt-secret}
    
    read -p "MONGO_URL (默認: mongodb://prod-mongo-url): " MONGO_URL_PROD
    MONGO_URL_PROD=${MONGO_URL_PROD:-mongodb://prod-mongo-url}
    
    # 設置環境變數
    echo ""
    echo "🚀 更新 prod 服務環境變數..."
    
    gcloud run services update mesh-proxy-server-prod \
        --region=asia-east1 \
        --set-env-vars="ENVIRONMENT=prod,PRIVATE_BUCKET_NAME=$PRIVATE_BUCKET_NAME_PROD,KEYFILE_BLOB_NAME=$KEYFILE_BLOB_NAME_PROD,MESH_GQL_ENDPOINT=$MESH_GQL_ENDPOINT_PROD,JWT_SECRET=$JWT_SECRET_PROD,MONGO_URL=$MONGO_URL_PROD" \
        --quiet
    
    echo "✅ prod 服務環境變數設置完成"
    
else
    echo "ℹ️  未找到 prod 服務（這是正常的，如果還沒有部署）"
fi

echo ""
echo "🎉 環境變數設置完成！"
echo ""
echo "📝 下一步:"
echo "1. 確保所有環境變數值都是正確的"
echo "2. 重新部署服務以應用新的環境變數"
echo "3. 檢查服務日誌確認沒有錯誤"
echo ""
echo "🔍 查看服務狀態:"
echo "  gcloud run services describe mesh-proxy-server-dev --region=asia-east1"
echo "  gcloud run services describe mesh-proxy-server-prod --region=asia-east1" 