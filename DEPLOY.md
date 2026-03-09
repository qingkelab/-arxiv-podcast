# Arxiv Podcast 部署配置

## 当前状态
- Web 服务已运行在 http://localhost:8080
- 使用 nohup 后台运行

## 访问方式
```bash
# 本地测试
curl http://localhost:8080

# 查看任务列表
curl http://localhost:8080/api/tasks

# 提交生成任务
curl -X POST http://localhost:8080/api/generate \
  -H "Content-Type: application/json" \
  -d '{"url":"https://arxiv.org/abs/2312.03689","voice":"xiaoxiao","resolution":"1920x1080"}'
```

## 生产部署（使用 systemd）

```bash
# 1. 创建服务文件
sudo tee /etc/systemd/system/arxiv-podcast.service > /dev/null << 'EOF'
[Unit]
Description=Arxiv Podcast Web Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace/arxiv-podcast
Environment=PORT=8080
Environment=HOST=0.0.0.0
Environment=PYTHONPATH=/root/.openclaw/workspace/arxiv-podcast
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/arxiv-podcast/web_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 2. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable arxiv-podcast
sudo systemctl start arxiv-podcast

# 3. 查看状态
sudo systemctl status arxiv-podcast
```

## Nginx 反向代理（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 防火墙设置

```bash
# 开放 8080 端口
sudo ufw allow 8080/tcp
# 或仅允许本地访问（配合 Nginx）
```
