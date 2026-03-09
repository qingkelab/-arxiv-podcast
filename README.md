# Arxiv Paper to Video Podcast

自动将 arxiv 论文转换为 3-5 分钟视频播客的应用。

## 功能

- 获取 arxiv 论文 HTML 版本
- AI 分析论文核心内容
- 生成口语化播客脚本
- 自动选取合适的论文图片
- TTS 语音合成
- 生成带图片切换的视频播客

## 安装

```bash
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env`，填入你的 API Key：

```bash
cp .env.example .env
```

编辑 `.env`：
```
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，用于第三方 API
```

## 使用

```bash
python main.py https://arxiv.org/abs/2401.12345
```

输出保存在 `output/{arxiv_id}/` 目录下。

## 输出文件

- `paper.html` - 原始论文 HTML
- `images/` - 提取的论文图片
- `script.json` - 生成的播客脚本
- `audio.mp3` - TTS 音频
- `podcast.mp4` - 最终视频播客
