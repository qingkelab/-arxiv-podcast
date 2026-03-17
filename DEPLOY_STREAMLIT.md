# 快速部署指南

## 方式一：Streamlit Cloud 一键部署

### 步骤 1：确保代码在 GitHub
代码已在 https://github.com/qingkelab/-arxiv-podcast

### 步骤 2：部署到 Streamlit Cloud
1. 访问 https://streamlit.io/cloud
2. 用 GitHub 登录
3. 点击 "New app"
4. 选择 Repository: `qingkelab/-arxiv-podcast`
5. Branch: `main`
6. Main file path: `app.py`
7. 点击 "Deploy"

### 步骤 3：配置环境变量（可选）
在 App 页面 → Settings → Secrets，添加：
```toml
KIMI_API_KEY = "sk-你的API密钥"
KIMICODE_API_KEY = "sk-你的Kimi Code密钥"
```

### 步骤 4：重启应用
点击 "Reboot" 或等待自动重启

---

## 方式二：使用已上传的部署包

1. 下载 `arxiv-podcast-deploy.tar.gz`（已发给你）
2. 解压到本地
3. 创建新的 GitHub 仓库
4. 上传代码
5. 按方式一部署

---

## 部署后访问

部署成功后会获得类似链接：
```
https://your-app-name.streamlit.app
```

---

## 注意事项

**Streamlit Cloud 免费版限制：**
- 内存：1GB
- 超时：30分钟（视频生成可能中断）
- 存储：临时（重启后文件丢失）

**建议用途：**
- 脚本生成（推荐）
- 音频生成（可能成功）
- 视频生成（可能超时，建议低分辨率）

---

## 替代方案

如果需要完整功能，使用已部署的：
- **自托管**: http://10.59.34.75:8080
- **Render**: 支持长时间任务
