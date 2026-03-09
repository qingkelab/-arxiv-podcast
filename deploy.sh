#!/bin/bash
# 部署脚本

echo "🚀 部署 Arxiv Podcast 服务..."

# 检查目录
cd /root/.openclaw/workspace/arxiv-podcast || exit 1

# 检查依赖
echo "📦 检查依赖..."
pip3 install --break-system-packages -q -r requirements.txt 2>/dev/null || pip3 install -q -r requirements.txt

# 停止旧服务
echo "🛑 停止旧服务..."
pkill -f web_server.py 2>/dev/null || true
sleep 1

# 启动新服务
echo "▶️  启动服务..."
export PORT=8080
export HOST=0.0.0.0
export PYTHONPATH=/root/.openclaw/workspace/arxiv-podcast

nohup python3 web_server.py > /var/log/arxiv-podcast.log 2>&1 &
echo $! > /var/run/arxiv-podcast.pid

sleep 2

# 检查服务状态
if curl -s http://localhost:8080 > /dev/null; then
    echo "✅ 服务启动成功！"
    echo "📍 访问地址: http://$(hostname -I | awk '{print $1}'):8080"
    echo "📖 API 文档: http://$(hostname -I | awk '{print $1}'):8080/docs"
else
    echo "❌ 服务启动失败，查看日志:"
    tail -20 /var/log/arxiv-podcast.log
fi
