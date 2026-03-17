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
- `.streamlit/config.toml` - 配置文件（已内置）

### 2. 部署到 Streamlit Cloud

1. 访问 https://streamlit.io/cloud
2. 用 GitHub 账号登录
3. 点击 "New app"
4. 选择你的仓库
5. 设置：
   - **Main file path**: `app.py`
   - **Secrets**: 可选（默认在界面输入 Kimi API Key）

### 3. 配置 Secrets（可选）

在 Streamlit Cloud 控制台：
```
Advanced settings → Secrets
```

如果你不想每次手动输入 API Key，可加：
```toml
KIMI_API_KEY = "your-api-key-here"
```

## 限制

**Streamlit Cloud 免费版：**
- 1GB 内存
- 超时限制（长时间任务可能中断）
- 无持久化存储（重启后文件丢失）

**适合场景：**
- 演示和测试
- 脚本生成/音频生成
- 视频生成（可能受限于 CPU 与超时）

## 替代方案

如果需要完整功能，建议使用：
- **自托管 VPS**（已部署）
- **Render Standard**（$7/月）

## 一键部署

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy)
