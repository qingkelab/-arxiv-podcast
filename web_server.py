"""
Web 服务模块 - 提供 HTTP API 和 Web 界面
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

# 添加到路径
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
import uvicorn

from fetcher import ArxivFetcher
from analyzer import ContentAnalyzer
from script_generator import PodcastScriptGenerator
from tts_engine import TTSEngine
from video_generator import VideoGenerator

app = FastAPI(title="Arxiv Podcast Generator", version="1.0.0")

# 存储任务状态
tasks = {}

# 请求模型
class ArxivRequest(BaseModel):
    url: str
    voice: Optional[str] = "xiaoxiao"
    resolution: Optional[str] = "1920x1080"

class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    created_at: str
    completed_at: Optional[str] = None
    output_files: Optional[dict] = None
    error: Optional[str] = None


def get_output_dir(arxiv_id: str) -> Path:
    """获取输出目录"""
    return Path("output") / arxiv_id


def update_task(task_id: str, status: str, progress: int, message: str, **kwargs):
    """更新任务状态"""
    tasks[task_id].update({
        "status": status,
        "progress": progress,
        "message": message,
        **kwargs
    })


async def process_paper_task(task_id: str, url: str, voice: str, resolution: str):
    """后台处理任务"""
    try:
        fetcher = ArxivFetcher()
        arxiv_id = fetcher.extract_arxiv_id(url)
        output_dir = get_output_dir(arxiv_id)
        
        update_task(task_id, "processing", 5, f"正在获取论文 {arxiv_id}...")
        
        # 1. 获取论文
        paper_data = fetcher.fetch(url, output_dir)
        html_path = output_dir / "paper.html"
        html_path.write_text(paper_data['raw_html'], encoding='utf-8')
        
        image_count = len([i for i in paper_data['images'] if i.get('local_path')])
        update_task(task_id, "processing", 20, f"已提取 {image_count} 张图片")
        
        # 2. 分析内容
        update_task(task_id, "processing", 30, "正在分析论文内容...")
        analyzer = ContentAnalyzer()
        analysis = analyzer.analyze(paper_data)
        
        analysis_path = output_dir / "analysis.json"
        analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding='utf-8')
        
        update_task(task_id, "processing", 45, f"核心贡献: {analysis.get('core_contribution', '')[:50]}...")
        
        # 3. 生成脚本
        update_task(task_id, "processing", 55, "正在生成播客脚本...")
        generator = PodcastScriptGenerator()
        script = generator.generate(analysis)
        
        script_path = output_dir / "script.json"
        script_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding='utf-8')
        
        text_path = output_dir / "script.txt"
        text_path.write_text(script['full_text'], encoding='utf-8')
        
        update_task(task_id, "processing", 65, f"脚本完成，预计时长: {script['estimated_duration_text']}")
        
        # 4. 生成语音
        update_task(task_id, "processing", 75, "正在合成语音...")
        tts = TTSEngine(voice=voice)
        tts_text = generator.get_full_text_for_tts(script)
        
        audio_path = output_dir / "audio.mp3"
        tts.generate(tts_text, audio_path)
        
        update_task(task_id, "processing", 85, "语音合成完成")
        
        # 5. 生成视频
        update_task(task_id, "processing", 90, "正在生成视频...")
        selected_images = analyzer.select_images_for_script(analysis, paper_data.get('images', []))
        
        if selected_images:
            res_map = {
                "1920x1080": (1920, 1080),
                "1080x1920": (1080, 1920),
                "1280x720": (1280, 720)
            }
            res = res_map.get(resolution, (1920, 1080))
            
            video_gen = VideoGenerator(resolution=res)
            video_path = output_dir / "podcast.mp4"
            video_gen.generate(script, audio_path, selected_images, video_path)
            
            update_task(task_id, "completed", 100, "视频播客生成完成！", 
                      completed_at=datetime.now().isoformat(),
                      output_files={
                          "html": str(html_path.relative_to("output")),
                          "analysis": str(analysis_path.relative_to("output")),
                          "script": str(script_path.relative_to("output")),
                          "audio": str(audio_path.relative_to("output")),
                          "video": str(video_path.relative_to("output"))
                      })
        else:
            update_task(task_id, "completed", 100, "音频生成完成（无可用图片）",
                      completed_at=datetime.now().isoformat(),
                      output_files={
                          "html": str(html_path.relative_to("output")),
                          "analysis": str(analysis_path.relative_to("output")),
                          "script": str(script_path.relative_to("output")),
                          "audio": str(audio_path.relative_to("output"))
                      })
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        update_task(task_id, "failed", 0, f"处理失败: {str(e)}", error=error_msg)


@app.get("/", response_class=HTMLResponse)
async def index():
    """主页 - 提供 Web 界面"""
    return HTMLResponse(content=INDEX_HTML)


@app.post("/api/generate")
async def generate(request: ArxivRequest, background_tasks: BackgroundTasks):
    """提交生成任务"""
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(request)}"
    
    tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "message": "任务已创建，等待处理...",
        "created_at": datetime.now().isoformat(),
        "arxiv_url": request.url
    }
    
    # 后台处理
    asyncio.create_task(process_paper_task(task_id, request.url, request.voice, request.resolution))
    
    return {"task_id": task_id, "message": "任务已提交"}


@app.get("/api/status/{task_id}", response_model=TaskStatus)
async def get_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskStatus(**tasks[task_id])


@app.get("/api/tasks")
async def list_tasks():
    """列出所有任务"""
    return list(tasks.values())


@app.get("/output/{arxiv_id}/{filename}")
async def get_output_file(arxiv_id: str, filename: str):
    """获取输出文件"""
    file_path = Path("output") / arxiv_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path)


# Web 界面 HTML
INDEX_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arxiv 论文转视频播客</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 40px;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .input-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #aaa;
            font-size: 14px;
        }
        input[type="text"], select {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: rgba(0,0,0,0.3);
            color: #fff;
            font-size: 16px;
            transition: all 0.3s;
        }
        input[type="text"]:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        .row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        button {
            width: 100%;
            padding: 16px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 8px;
            color: #fff;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .progress-container {
            display: none;
            margin-top: 20px;
        }
        .progress-container.active {
            display: block;
        }
        .progress-bar {
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
            transition: width 0.3s ease;
            width: 0%;
        }
        .progress-text {
            text-align: center;
            margin-top: 10px;
            color: #aaa;
        }
        .result-container {
            display: none;
            margin-top: 20px;
            padding: 20px;
            background: rgba(0,255,0,0.1);
            border-radius: 8px;
            border: 1px solid rgba(0,255,0,0.3);
        }
        .result-container.active {
            display: block;
        }
        .result-container a {
            color: #667eea;
            text-decoration: none;
        }
        .result-container a:hover {
            text-decoration: underline;
        }
        .error-container {
            display: none;
            margin-top: 20px;
            padding: 20px;
            background: rgba(255,0,0,0.1);
            border-radius: 8px;
            border: 1px solid rgba(255,0,0,0.3);
            color: #ff6b6b;
        }
        .error-container.active {
            display: block;
        }
        .task-list {
            margin-top: 20px;
        }
        .task-item {
            padding: 15px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .task-status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .status-pending { background: #f0ad4e; color: #000; }
        .status-processing { background: #5bc0de; color: #000; }
        .status-completed { background: #5cb85c; color: #fff; }
        .status-failed { background: #d9534f; color: #fff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Arxiv Podcast</h1>
        <p class="subtitle">将学术论文转换为视频播客</p>
        
        <div class="card">
            <div class="input-group">
                <label>Arxiv 论文链接</label>
                <input type="text" id="url" placeholder="https://arxiv.org/abs/2401.12345" 
                       value="https://arxiv.org/abs/2312.03689">
            </div>
            
            <div class="row">
                <div class="input-group">
                    <label>语音选择</label>
                    <select id="voice">
                        <option value="xiaoxiao">晓晓 (女声-活泼)</option>
                        <option value="xiaoyi">晓伊 (女声-温柔)</option>
                        <option value="yunjian">云健 (男声-新闻)</option>
                        <option value="yunxi">云希 (男声-年轻)</option>
                        <option value="yunxia">云夏 (男声-讲故事)</option>
                    </select>
                </div>
                <div class="input-group">
                    <label>视频分辨率</label>
                    <select id="resolution">
                        <option value="1920x1080">1920x1080 (横屏)</option>
                        <option value="1080x1920">1080x1920 (竖屏-短视频)</option>
                        <option value="1280x720">1280x720 (高清)</option>
                    </select>
                </div>
            </div>
            
            <button id="generateBtn" onclick="startGeneration()">开始生成</button>
            
            <div class="progress-container" id="progressContainer">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="progress-text" id="progressText">准备中...</div>
            </div>
            
            <div class="result-container" id="resultContainer">
                <strong>✅ 生成完成！</strong><br><br>
                <div id="resultLinks"></div>
            </div>
            
            <div class="error-container" id="errorContainer">
                <strong>❌ 生成失败</strong><br><br>
                <div id="errorText"></div>
            </div>
        </div>
        
        <div class="card">
            <h3>📋 任务列表</h3>
            <div class="task-list" id="taskList">
                <p style="color: #666; text-align: center;">暂无任务</p>
            </div>
        </div>
    </div>

    <script>
        let currentTaskId = null;
        let statusInterval = null;
        
        async function startGeneration() {
            const url = document.getElementById('url').value;
            const voice = document.getElementById('voice').value;
            const resolution = document.getElementById('resolution').value;
            
            if (!url) {
                alert('请输入 Arxiv 链接');
                return;
            }
            
            // 重置 UI
            document.getElementById('generateBtn').disabled = true;
            document.getElementById('progressContainer').classList.add('active');
            document.getElementById('resultContainer').classList.remove('active');
            document.getElementById('errorContainer').classList.remove('active');
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, voice, resolution })
                });
                
                const data = await response.json();
                currentTaskId = data.task_id;
                
                // 开始轮询状态
                statusInterval = setInterval(checkStatus, 1000);
                
            } catch (error) {
                showError(error.message);
            }
        }
        
        async function checkStatus() {
            if (!currentTaskId) return;
            
            try {
                const response = await fetch(`/api/status/${currentTaskId}`);
                const data = await response.json();
                
                // 更新进度
                document.getElementById('progressFill').style.width = data.progress + '%';
                document.getElementById('progressText').textContent = data.message;
                
                if (data.status === 'completed') {
                    clearInterval(statusInterval);
                    showResult(data.output_files, data.task_id);
                    document.getElementById('generateBtn').disabled = false;
                    loadTaskList();
                } else if (data.status === 'failed') {
                    clearInterval(statusInterval);
                    showError(data.error || '未知错误');
                    document.getElementById('generateBtn').disabled = false;
                }
                
            } catch (error) {
                console.error('检查状态失败:', error);
            }
        }
        
        function showResult(files, taskId) {
            document.getElementById('progressContainer').classList.remove('active');
            document.getElementById('resultContainer').classList.add('active');
            
            let linksHtml = '';
            if (files.video) {
                linksHtml += `<a href="/output/${files.video}" target="_blank">📹 下载视频</a><br>`;
            }
            if (files.audio) {
                linksHtml += `<a href="/output/${files.audio}" target="_blank">🎵 下载音频</a><br>`;
            }
            if (files.script) {
                linksHtml += `<a href="/output/${files.script}" target="_blank">📝 查看脚本</a><br>`;
            }
            
            document.getElementById('resultLinks').innerHTML = linksHtml;
        }
        
        function showError(message) {
            document.getElementById('progressContainer').classList.remove('active');
            document.getElementById('errorContainer').classList.add('active');
            document.getElementById('errorText').textContent = message;
        }
        
        async function loadTaskList() {
            try {
                const response = await fetch('/api/tasks');
                const tasks = await response.json();
                
                const listEl = document.getElementById('taskList');
                if (tasks.length === 0) {
                    listEl.innerHTML = '<p style="color: #666; text-align: center;">暂无任务</p>';
                    return;
                }
                
                listEl.innerHTML = tasks.slice(-10).reverse().map(task => {
                    const statusClass = `status-${task.status}`;
                    const statusText = {
                        'pending': '等待中',
                        'processing': '处理中',
                        'completed': '已完成',
                        'failed': '失败'
                    }[task.status];
                    
                    return `
                        <div class="task-item">
                            <div>
                                <div style="font-size: 12px; color: #888; margin-bottom: 4px;">
                                    ${new Date(task.created_at).toLocaleString()}
                                </div>
                                <div style="font-size: 14px;">${task.message}</div>
                            </div>
                            <span class="task-status ${statusClass}">${statusText}</span>
                        </div>
                    `;
                }).join('');
                
            } catch (error) {
                console.error('加载任务列表失败:', error);
            }
        }
        
        // 页面加载时获取任务列表
        loadTaskList();
        setInterval(loadTaskList, 5000);
    </script>
</body>
</html>
"""


def main():
    """启动 Web 服务"""
    port = int(os.getenv('PORT', 8080))
    host = os.getenv('HOST', '0.0.0.0')
    
    print(f"🚀 启动 Arxiv Podcast Web 服务...")
    print(f"📍 访问地址: http://{host}:{port}")
    print(f"📖 API 文档: http://{host}:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
