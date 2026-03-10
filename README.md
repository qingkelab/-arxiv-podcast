# Arxiv Paper to Video Podcast

自动将 arxiv 论文转换为 3-5 分钟视频播客的应用。

## 功能特性

- 🌐 **Web 界面** - 浏览器上传，实时进度，任务管理
- 🔑 **前端 API 配置** - 支持用户在前端输入自己的 Kimi API Key
- 🎭 **双人对话播客** - 小北(主持人) & 阿杰(嘉宾) 的对话形式
- 🎤 **单人播客** - 传统的单人解说风格
- 🤖 **AI 分析** - 自动提取论文核心内容
- ✍️ **脚本生成** - 口语化 3-5 分钟播客脚本
- 🔊 **语音合成** - 多种中文语音可选，双人模式自动分配不同音色
- 🎬 **视频生成** - 自动配图，支持横屏/竖屏

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行

**Web 界面（推荐）：**
```bash
python app.py
# 访问 http://localhost:8501
```

在界面中：
1. 输入你的 Kimi API Key
2. 选择播客风格（单人或双人对话）
3. 粘贴 arxiv 论文链接
4. 点击生成

**交互式 CLI：**
```bash
python cli.py
```

**命令行模式：**
```bash
python cli.py -u https://arxiv.org/abs/2312.03689
```

## 播客风格

### 🎤 单人播客
传统的单人解说风格，适合快速了解论文内容。

### 🎭 双人对话 (小北♀ & 阿杰♂)
- **小北(女)**：主持人，科技爱好者，好奇心强，善于提问，语气活泼亲和
- **阿杰(男)**：嘉宾，AI研究员，专业背景，善于深入浅出解释技术，语气沉稳有温度

两人有自然的互动、插话、呼应，像朋友间的真实对话。

## 部署

### Streamlit Cloud（推荐）
```bash
./deploy-streamlit.sh
```

### 自托管
```bash
./deploy.sh
```

### Render（一键部署）
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/qingkelab/-arxiv-podcast)

详见 [RENDER_DEPLOY.md](RENDER_DEPLOY.md)

## 使用方式

详见 [完整文档](#)

## 许可证

MIT
