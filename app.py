"""
Streamlit 版本 - 更简单的部署方式
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

import streamlit as st

# 添加到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from fetcher import ArxivFetcher
from analyzer import ContentAnalyzer
from script_generator import PodcastScriptGenerator
from tts_engine import TTSEngine
from video_generator import VideoGenerator

# 页面配置
st.set_page_config(
    page_title="Arxiv Podcast Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 样式
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    .success-box {
        padding: 1rem;
        background: rgba(0,255,0,0.1);
        border-radius: 8px;
        border: 1px solid rgba(0,255,0,0.3);
    }
    .error-box {
        padding: 1rem;
        background: rgba(255,0,0,0.1);
        border-radius: 8px;
        border: 1px solid rgba(255,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# 初始化 session state
if 'tasks' not in st.session_state:
    st.session_state.tasks = {}


def update_task(task_id, status, progress, message, **kwargs):
    """更新任务状态"""
    st.session_state.tasks[task_id] = {
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "message": message,
        "created_at": datetime.now().isoformat(),
        **kwargs
    }


def process_paper(url, voice, resolution, task_id):
    """处理论文"""
    try:
        fetcher = ArxivFetcher()
        arxiv_id = fetcher.extract_arxiv_id(url)
        output_dir = Path("output") / arxiv_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 获取论文
        update_task(task_id, "processing", 10, f"正在获取论文 {arxiv_id}...")
        paper_data = fetcher.fetch(url, output_dir)
        html_path = output_dir / "paper.html"
        html_path.write_text(paper_data['raw_html'], encoding='utf-8')
        
        # 2. 分析内容
        update_task(task_id, "processing", 30, "正在分析论文内容...")
        analyzer = ContentAnalyzer()
        analysis = analyzer.analyze(paper_data)
        
        analysis_path = output_dir / "analysis.json"
        analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding='utf-8')
        
        # 3. 生成脚本
        update_task(task_id, "processing", 50, "正在生成播客脚本...")
        generator = PodcastScriptGenerator()
        script = generator.generate(analysis)
        
        script_path = output_dir / "script.json"
        script_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding='utf-8')
        
        text_path = output_dir / "script.txt"
        text_path.write_text(script['full_text'], encoding='utf-8')
        
        # 4. 生成语音
        update_task(task_id, "processing", 70, "正在合成语音...")
        tts = TTSEngine(voice=voice)
        tts_text = generator.get_full_text_for_tts(script)
        
        audio_path = output_dir / "audio.mp3"
        tts.generate(tts_text, audio_path)
        
        # 5. 生成视频
        update_task(task_id, "processing", 90, "正在生成视频...")
        selected_images = analyzer.select_images_for_script(analysis, paper_data.get('images', []))
        
        video_path = None
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
        
        update_task(task_id, "completed", 100, "生成完成！",
                   output_dir=str(output_dir),
                   audio=str(audio_path),
                   video=str(video_path) if video_path else None,
                   script=str(text_path))
        
        return True
        
    except Exception as e:
        import traceback
        update_task(task_id, "failed", 0, f"处理失败: {str(e)}",
                   error=f"{str(e)}\n{traceback.format_exc()}")
        return False


def main():
    # 标题
    st.markdown('<h1 class="main-header">🎙️ Arxiv Podcast</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">将学术论文转换为视频播客</p>', unsafe_allow_html=True)
    
    # 检查 API Key
    if not os.getenv('OPENAI_API_KEY'):
        st.error("⚠️ 未设置 OPENAI_API_KEY 环境变量")
        st.info("请在 Streamlit Secrets 或 .env 文件中配置 API Key")
        return
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        
        voice = st.selectbox(
            "选择语音",
            options=["xiaoxiao", "xiaoyi", "yunjian", "yunxi", "yunxia"],
            format_func=lambda x: {
                "xiaoxiao": "晓晓 (女声-活泼)",
                "xiaoyi": "晓伊 (女声-温柔)",
                "yunjian": "云健 (男声-新闻)",
                "yunxi": "云希 (男声-年轻)",
                "yunxia": "云夏 (男声-讲故事)"
            }[x]
        )
        
        resolution = st.selectbox(
            "视频分辨率",
            options=["1920x1080", "1080x1920", "1280x720"],
            format_func=lambda x: {
                "1920x1080": "1920x1080 (横屏)",
                "1080x1920": "1080x1920 (竖屏-短视频)",
                "1280x720": "1280x720 (高清)"
            }[x]
        )
        
        st.divider()
        st.markdown("### 📋 使用说明")
        st.markdown("""
        1. 输入 arxiv 论文链接
        2. 选择语音和分辨率
        3. 点击生成按钮
        4. 等待处理完成
        5. 下载生成的文件
        """)
    
    # 主界面
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 输入框
        url = st.text_input(
            "Arxiv 论文链接",
            placeholder="https://arxiv.org/abs/2312.03689",
            help="输入完整的 arxiv 论文 URL"
        )
        
        # 生成按钮
        if st.button("🚀 开始生成", type="primary", use_container_width=True):
            if not url:
                st.error("请输入论文链接")
            else:
                task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                update_task(task_id, "pending", 0, "准备开始...")
                
                # 显示进度
                progress_placeholder = st.empty()
                status_placeholder = st.empty()
                
                # 运行处理
                with st.spinner("正在处理..."):
                    success = process_paper(url, voice, resolution, task_id)
                
                # 显示结果
                task = st.session_state.tasks.get(task_id, {})
                
                if success:
                    st.success("✅ 生成完成！")
                    
                    # 下载按钮
                    output_dir = Path(task.get('output_dir', ''))
                    
                    col_audio, col_video, col_script = st.columns(3)
                    
                    with col_audio:
                        audio_path = task.get('audio')
                        if audio_path and Path(audio_path).exists():
                            with open(audio_path, 'rb') as f:
                                st.download_button(
                                    "🔊 下载音频",
                                    f.read(),
                                    file_name=f"{output_dir.name}_audio.mp3",
                                    mime="audio/mp3",
                                    use_container_width=True
                                )
                    
                    with col_video:
                        video_path = task.get('video')
                        if video_path and Path(video_path).exists():
                            with open(video_path, 'rb') as f:
                                st.download_button(
                                    "🎬 下载视频",
                                    f.read(),
                                    file_name=f"{output_dir.name}_podcast.mp4",
                                    mime="video/mp4",
                                    use_container_width=True
                                )
                    
                    with col_script:
                        script_path = task.get('script')
                        if script_path and Path(script_path).exists():
                            with open(script_path, 'r', encoding='utf-8') as f:
                                st.download_button(
                                    "📝 下载脚本",
                                    f.read(),
                                    file_name=f"{output_dir.name}_script.txt",
                                    mime="text/plain",
                                    use_container_width=True
                                )
                    
                    # 显示脚本预览
                    if script_path:
                        with open(script_path, 'r', encoding='utf-8') as f:
                            script_content = f.read()
                        with st.expander("📄 查看脚本"):
                            st.text_area("播客脚本", script_content, height=300)
                
                else:
                    st.error(f"❌ 生成失败: {task.get('message', '未知错误')}")
                    with st.expander("查看错误详情"):
                        st.code(task.get('error', '无详细信息'))
    
    with col2:
        st.subheader("📊 任务状态")
        
        if st.session_state.tasks:
            for task_id, task in list(st.session_state.tasks.items())[-5:]:
                status_color = {
                    "pending": "⏳",
                    "processing": "🔄",
                    "completed": "✅",
                    "failed": "❌"
                }.get(task['status'], "⏳")
                
                st.markdown(f"""
                <div style="padding: 10px; background: rgba(255,255,255,0.05); 
                            border-radius: 8px; margin-bottom: 10px;">
                    <small style="color: #888;">{task_id}</small><br>
                    {status_color} {task['message'][:50]}...
                    <div style="margin-top: 5px;">
                        <div style="background: rgba(255,255,255,0.1); height: 4px; border-radius: 2px;">
                            <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                                        height: 100%; border-radius: 2px; width: {task['progress']}%;">
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("暂无任务")


if __name__ == "__main__":
    main()
