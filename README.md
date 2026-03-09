# Arxiv Paper to Video Podcast

自动将 arxiv 论文转换为 3-5 分钟视频播客的应用。

## 功能特性

- 🌐 **Web 界面** - 浏览器上传，实时进度，任务管理
- 🖥️ **增强 CLI** - 进度条、彩色输出、交互式向导
- 🤖 **AI 分析** - 自动提取论文核心内容
- ✍️ **脚本生成** - 口语化 3-5 分钟播客脚本
- 🔊 **语音合成** - 多种中文语音可选
- 🎬 **视频生成** - 自动配图，支持横屏/竖屏

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env 填入你的 OpenAI API Key
```

### 3. 运行

**Web 界面（推荐）：**
```bash
python cli.py --web
# 访问 http://localhost:8080
```

**交互式 CLI：**
```bash
python cli.py
```

**命令行模式：**
```bash
python cli.py -u https://arxiv.org/abs/2312.03689
```

## 部署

### 自托管（推荐）
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
