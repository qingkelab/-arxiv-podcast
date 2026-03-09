#!/bin/bash
# Streamlit Cloud 部署脚本
# 使用方法: ./deploy-streamlit.sh YOUR_API_KEY

API_KEY=${1:-""}

if [ -z "$API_KEY" ]; then
    echo "❌ 请提供 OpenAI API Key"
    echo "用法: ./deploy-streamlit.sh sk-xxxxxxxx"
    exit 1
fi

echo "🚀 开始部署到 Streamlit Cloud..."
echo ""
echo "步骤 1: 检查依赖..."

# 检查 streamlit 是否安装
if ! command -v streamlit &> /dev/null; then
    echo "安装 streamlit..."
    pip install streamlit -q
fi

echo "✓ 依赖检查完成"
echo ""
echo "步骤 2: 本地测试..."
timeout 5 streamlit run app.py --server.headless true &
PID=$!
sleep 3

if kill -0 $PID 2>/dev/null; then
    echo "✓ 本地测试通过"
    kill $PID 2>/dev/null
else
    echo "⚠️ 本地测试失败，继续部署..."
fi

echo ""
echo "步骤 3: 部署到 Streamlit Cloud"
echo ""
echo "请按以下步骤操作:"
echo ""
echo "1. 访问 https://streamlit.io/cloud"
echo "2. 用 GitHub 账号登录"
echo "3. 点击 'New app'"
echo "4. 选择 Repository: qingkelab/-arxiv-podcast"
echo "5. Branch: main"
echo "6. Main file path: app.py"
echo "7. 点击 'Advanced settings...'"
echo "8. 添加 Secrets:"
echo "   OPENAI_API_KEY = $API_KEY"
echo "9. 点击 'Deploy!'"
echo ""
echo "或者使用 Streamlit CLI (如果已安装):"
echo "   streamlit deploy app.py"
echo ""
echo "📋 部署信息:"
echo "   仓库: https://github.com/qingkelab/-arxiv-podcast"
echo "   分支: main"
echo "   主文件: app.py"
echo ""
echo "部署完成后，你将获得类似链接:"
echo "   https://arxiv-podcast-xxxxx.streamlit.app"
