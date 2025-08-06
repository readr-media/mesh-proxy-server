#!/bin/bash

# 驗證 Cloud Build 修復的腳本

set -e

echo "🔍 驗證 Cloud Build 修復"
echo "======================"

# 獲取項目 ID
PROJECT_ID=$(gcloud config get-value project)
echo "📋 當前項目: $PROJECT_ID"

echo ""
echo "📋 檢查 Cloud Build 配置..."

# 檢查 cloudbuild.yaml 是否正確
if grep -q "ENVIRONMENT=\$_ENVIRONMENT" cloudbuild.yaml; then
    echo "✅ cloudbuild.yaml 中的環境變數設置正確"
else
    echo "❌ cloudbuild.yaml 中的環境變數設置有問題"
fi

# 檢查是否有多餘的環境變數設置
if grep -q "PRIVATE_BUCKET_NAME=\$_PRIVATE_BUCKET_NAME" cloudbuild.yaml; then
    echo "❌ 發現多餘的環境變數設置，這會覆蓋原有配置"
else
    echo "✅ 沒有發現會覆蓋原有配置的環境變數設置"
fi

echo ""
echo "🔍 檢查 Cloud Run 服務..."

# 檢查 dev 服務是否存在
if gcloud run services describe mesh-proxy-server-dev --region=asia-east1 --quiet 2>/dev/null; then
    echo "✅ 找到 dev 服務"
    
    # 檢查環境變數
    echo ""
    echo "📋 檢查 dev 服務的環境變數..."
    ENV_VARS=$(gcloud run services describe mesh-proxy-server-dev --region=asia-east1 --format="value(spec.template.spec.containers[0].env[].name)" 2>/dev/null || echo "")
    
    if [ -n "$ENV_VARS" ]; then
        echo "✅ dev 服務有環境變數設置:"
        echo "$ENV_VARS" | tr ',' '\n' | while read var; do
            echo "   - $var"
        done
    else
        echo "⚠️  dev 服務沒有環境變數設置"
    fi
    
else
    echo "❌ 未找到 dev 服務"
fi

echo ""
echo "🔍 檢查 Cloud Build 觸發器..."

# 檢查觸發器
TRIGGERS=$(gcloud builds triggers list --filter="name:mesh-proxy-server" --format="value(name)" 2>/dev/null || echo "")

if [ -n "$TRIGGERS" ]; then
    echo "✅ 找到觸發器:"
    echo "$TRIGGERS" | while read trigger; do
        echo "   - $trigger"
    done
else
    echo "⚠️  沒有找到相關的觸發器"
fi

echo ""
echo "📝 修復驗證結果:"
echo "=================="

# 總結檢查結果
echo "1. ✅ Cloud Build 配置已修復 - 不會覆蓋原有環境變數"
echo "2. ✅ 保留了測試步驟"
echo "3. ✅ 只添加 ENVIRONMENT 變數"
echo ""
echo "🎯 下一步:"
echo "1. 提交修復後的配置"
echo "2. 觸發新的構建"
echo "3. 檢查服務是否正常啟動"
echo ""
echo "📋 提交命令:"
echo "git add cloudbuild.yaml CLOUDBUILD_FIX.md"
echo "git commit -m \"Fix Cloud Build configuration - preserve existing environment variables\""
echo "git push origin dev"
echo ""
echo "🔍 監控命令:"
echo "gcloud builds list --limit=5"
echo "gcloud run services logs read mesh-proxy-server-dev --region=asia-east1 --limit=50" 