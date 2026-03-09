# Streamlit 部署

## 本地运行

```bash
pip install streamlit
streamlit run app.py
```

访问 http://localhost:8501

## 部署到 Streamlit Cloud（免费）

### 1. 准备仓库
确保 GitHub 仓库包含：
- `app.py` - Streamlit 主程序
- `requirements.txt` - 依赖列表
- `.streamlit/config.toml` - 配置文件（可选）

### 2. 创建 Streamlit 配置文件

```bash
mkdir -p .streamlit
cat > .streamlit/config.toml << 'EOF'
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[theme]
primaryColor = "#667eea"
backgroundColor = "#0e1117"
secondaryBackgroundColor = "#1e1e2e"
textColor = "#fafafa"
font = "sans serif"
EOF
```

### 3. 部署到 Streamlit Cloud

1. 访问 https://streamlit.io/cloud
2. 用 GitHub 账号登录
3. 点击 "New app"
4. 选择你的仓库
5. 设置：
   - **Main file path**: `app.py`
   - **Secrets**: 添加 `OPENAI_API_KEY`

### 4. 配置 Secrets

在 Streamlit Cloud 控制台：
```
Advanced settings → Secrets
```

添加：
```toml
OPENAI_API_KEY = "your-api-key-here"
```

## 限制

**Streamlit Cloud 免费版：**
- 1GB 内存
- 超时限制（长时间任务可能中断）
- 无持久化存储（重启后文件丢失）

**适合场景：**
- 演示和测试
- 短时间任务（< 30 分钟）
- 脚本生成（不生成视频）

## 替代方案

如果需要完整功能，建议使用：
- **自托管 VPS**（已部署）
- **Render Standard**（$7/月）

## 一键部署

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy)
