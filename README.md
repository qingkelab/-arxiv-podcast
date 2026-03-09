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
python cli.py -u https://arxiv.org/abs/2312.03689 -v xiaoxiao -r 1080x1920
```

## 使用方式

### Web 界面

```bash
python cli.py --web
```

功能：
- 浏览器输入 arxiv 链接
- 实时查看处理进度
- 选择语音和分辨率
- 下载生成的视频/音频/脚本
- 任务历史列表

### 交互式 CLI

```bash
python cli.py
```

向导式操作，引导你：
1. 输入 arxiv 链接
2. 选择语音（5种中文语音）
3. 选择分辨率（横屏/竖屏）
4. 实时进度显示
5. 结果汇总

### 命令行模式

```bash
# 基础用法
python cli.py -u https://arxiv.org/abs/2312.03689

# 指定语音和分辨率
python cli.py -u https://arxiv.org/abs/2312.03689 \
              -v yunxi \
              -r 1080x1920

# 只生成音频（跳过视频）
python cli.py -u https://arxiv.org/abs/2312.03689 --skip-video

# 查看帮助
python cli.py --help
```

## 语音选项

| 选项 | 名称 | 风格 |
|------|------|------|
| xiaoxiao | 晓晓 | 女声，活泼自然 |
| xiaoyi | 晓伊 | 女声，温柔亲切 |
| yunjian | 云健 | 男声，新闻播报 |
| yunxi | 云希 | 男声，年轻活力 |
| yunxia | 云夏 | 男声，讲故事 |

## 分辨率选项

| 选项 | 尺寸 | 适用场景 |
|------|------|----------|
| 1920x1080 | 横屏 16:9 | YouTube/B站 |
| 1080x1920 | 竖屏 9:16 | 抖音/快手/视频号 |
| 1280x720 | 横屏 16:9 | 快速预览 |

## API 接口

启动 Web 服务后，可使用 HTTP API：

```bash
# 提交任务
POST /api/generate
{
  "url": "https://arxiv.org/abs/2312.03689",
  "voice": "xiaoxiao",
  "resolution": "1920x1080"
}

# 查询状态
GET /api/status/{task_id}

# 获取文件
GET /output/{arxiv_id}/{filename}
```

## 输出文件

```
output/{arxiv_id}/
├── paper.html          # 原始论文 HTML
├── images/             # 提取的图片
├── analysis.json       # AI 分析结果
├── script.json         # 结构化脚本
├── script.txt          # 播客脚本文本
├── audio.mp3           # 语音文件
└── podcast.mp4         # 最终视频
```

## 技术架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Web UI    │     │  CLI Tool   │     │   HTTP API  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       └───────────────────┼───────────────────┘
                           ▼
              ┌─────────────────────────┐
              │    ArxivPodcastCLI      │
              └───────────┬─────────────┘
                          ▼
        ┌─────────────────────────────────────┐
        │  1. Fetch  →  2. Analyze           │
        │  3. Script →  4. TTS → 5. Video    │
        └─────────────────────────────────────┘
```

## 环境变量

| 变量 | 说明 | 必需 |
|------|------|------|
| OPENAI_API_KEY | OpenAI API Key | 是 |
| OPENAI_BASE_URL | API 基础 URL | 否 |
| PORT | Web 服务端口 | 否 (默认 8080) |
| HOST | Web 服务地址 | 否 (默认 0.0.0.0) |

## 许可证

MIT
