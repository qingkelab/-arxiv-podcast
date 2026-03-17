"""
Streamlit 优化版 - 轻量级，适合 Cloud 部署
支持前端配置 Kimi API 和双人对话播客
"""
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import tempfile

import streamlit as st

# 页面配置
st.set_page_config(
    page_title="Arxiv Podcast Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# CSS 样式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;600;700&family=ZCOOL+XiaoWei&display=swap');
    .main-header {
        font-family: 'ZCOOL XiaoWei', serif;
        font-size: 2.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        background: linear-gradient(90deg, #0f172a 0%, #2563eb 55%, #0ea5e9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.3rem;
    }
    .subtitle {
        text-align: center;
        color: #475569;
        margin-bottom: 2rem;
        font-size: 1.05rem;
        font-family: 'Noto Sans SC', sans-serif;
    }
    .stProgress > div > div {
        background: linear-gradient(90deg, #0ea5e9 0%, #2563eb 100%) !important;
    }
    .api-input {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
    }
    .script-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        white-space: pre-wrap;
    }
    .dialogue-xiaobei {
        background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%);
        color: white;
        padding: 0.8rem 1rem;
        border-radius: 12px 12px 12px 4px;
        margin: 0.5rem 0;
        max-width: 85%;
    }
    .dialogue-ajie {
        background: #f0f0f0;
        color: #333;
        padding: 0.8rem 1rem;
        border-radius: 12px 12px 4px 12px;
        margin: 0.5rem 0 0.5rem auto;
        max-width: 85%;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.75rem 1rem;
    }
    .hint-badge {
        display: inline-block;
        background: #e0f2fe;
        color: #075985;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def extract_arxiv_id(url: str) -> Optional[str]:
    """提取 arxiv ID"""
    patterns = [
        r'arxiv\.org/abs/(\d+\.\d+)',
        r'arxiv\.org/html/(\d+\.\d+)',
        r'arxiv\.org/pdf/(\d+\.\d+)',
        r'(\d{4}\.\d{4,5})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def render_dialogue(dialogue: list):
    """渲染对话格式脚本"""
    for line in dialogue:
        speaker = line['speaker']
        text = line['text']
        name = line['speaker_name']
        
        if speaker == 'xiaobei':
            st.markdown(f"""
            <div style="display: flex; align-items: flex-start; margin: 0.5rem 0;">
                <div style="width: 36px; height: 36px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                            color: white; font-weight: bold; margin-right: 0.5rem; flex-shrink: 0;">北</div>
                <div class="dialogue-xiaobei"><strong>小北:</strong> {text}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; align-items: flex-start; justify-content: flex-end; margin: 0.5rem 0;">
                <div class="dialogue-ajie"><strong>阿杰:</strong> {text}</div>
                <div style="width: 36px; height: 36px; background: #666; 
                            border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                            color: white; font-weight: bold; margin-left: 0.5rem; flex-shrink: 0;">杰</div>
            </div>
            """, unsafe_allow_html=True)


def _parse_resolution(resolution_text: str) -> tuple:
    parts = resolution_text.lower().split('x')
    if len(parts) != 2:
        return (1920, 1080)
    try:
        return (int(parts[0]), int(parts[1]))
    except ValueError:
        return (1920, 1080)


def _segments_from_dialogue(dialogue: list) -> list:
    """将对话粗分为 5 段，便于配图生成视频"""
    if not dialogue:
        return []
    
    buckets = 5
    size = max(1, len(dialogue) // buckets)
    types = ['intro', 'problem', 'method', 'results', 'outro']
    type_names = {
        'intro': '开场',
        'problem': '问题背景',
        'method': '方法介绍',
        'results': '结果与意义',
        'outro': '结尾'
    }
    
    segments = []
    for i in range(buckets):
        start = i * size
        end = (i + 1) * size if i < buckets - 1 else len(dialogue)
        chunk = dialogue[start:end]
        if not chunk:
            continue
        text = ' '.join([c.get('text', '') for c in chunk]).strip()
        if not text:
            continue
        word_count = len(text.split())
        duration = word_count / 150 * 60
        seg_type = types[i] if i < len(types) else 'general'
        segments.append({
            'type': seg_type,
            'type_name': type_names.get(seg_type, seg_type),
            'text': text,
            'word_count': word_count,
            'estimated_duration_seconds': round(duration, 1)
        })
    
    return segments


def _estimate_duration_text(script: dict) -> str:
    sec = script.get('estimated_duration_seconds')
    if sec is None:
        return "未知"
    return f"{sec/60:.1f} 分钟"


def _length_metric(script: dict) -> int:
    return int(script.get('total_char_count') or script.get('total_word_count') or 0)


def _validate_api_key(api_key: str, base_url: str) -> tuple:
    if not api_key:
        return False, "API Key 为空"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        _ = client.models.list()
        return True, "API Key 有效"
    except Exception as e:
        return False, str(e)


def main():
    # 标题
    st.markdown('<h1 class="main-header">Arxiv Podcast Studio</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">把论文变成 3-5 分钟的中文双人播客与视频</p>', unsafe_allow_html=True)
    
    # 初始化 session state
    if 'api_configured' not in st.session_state:
        st.session_state.api_configured = False
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        
        # API 配置
        with st.expander("🔑 API 配置", expanded=True):
            platform = st.selectbox(
                "平台选择",
                ["Moonshot (CN)", "Moonshot (Global)", "Kimi Code"],
                index=0,
                help="Moonshot 通用模型 或 Kimi Code 编程平台",
                key="platform_input"
            )
            
            platform_defaults = {
                "Moonshot (CN)": {
                    "base_url": "https://api.moonshot.cn/v1",
                    "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
                },
                "Moonshot (Global)": {
                    "base_url": "https://api.moonshot.ai/v1",
                    "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
                },
                "Kimi Code": {
                    "base_url": "https://api.kimi.com/coding/v1",
                    "models": ["kimi-for-coding"]
                }
            }
            
            if "platform_last" not in st.session_state:
                st.session_state.platform_last = platform
            
            if platform != st.session_state.platform_last:
                st.session_state.base_url_input = platform_defaults[platform]["base_url"]
                st.session_state.analyze_model_input = platform_defaults[platform]["models"][0]
                st.session_state.script_model_input = platform_defaults[platform]["models"][0]
                st.session_state.platform_last = platform
            
            api_key_env = os.getenv("KIMI_API_KEY", "")
            if platform == "Kimi Code":
                api_key_env = os.getenv("KIMICODE_API_KEY", os.getenv("KIMI_CODE_API_KEY", ""))
            
            api_key = st.text_input(
                "Kimi API Key",
                type="password",
                placeholder="sk-...",
                value=api_key_env,
                help="你的 Kimi API Key，不会存储在服务器上",
                key="api_key_input"
            )
            
            base_url = st.text_input(
                "API Base URL",
                value=platform_defaults[platform]["base_url"],
                help="Kimi API 地址（不同平台不同地址）",
                key="base_url_input"
            )
            
            analyze_model = st.selectbox(
                "分析模型",
                platform_defaults[platform]["models"],
                index=0,
                help="用于分析论文的模型",
                key="analyze_model_input"
            )
            
            script_model = st.selectbox(
                "脚本生成模型",
                platform_defaults[platform]["models"],
                index=0,
                help="用于生成播客脚本的模型",
                key="script_model_input"
            )
            
            col_api_1, col_api_2 = st.columns(2)
            with col_api_1:
                if st.button("✅ 校验 API Key", use_container_width=True):
                    ok, msg = _validate_api_key(api_key, base_url)
                    if ok:
                        st.success("API Key 有效")
                    else:
                        st.error(f"API Key 无效或无法连接：{msg}")
            with col_api_2:
                # 保存配置按钮
                if st.button("💾 保存配置", use_container_width=True):
                    if api_key:
                        st.session_state.api_key = api_key
                        st.session_state.base_url = base_url
                        st.session_state.analyze_model = analyze_model
                        st.session_state.script_model = script_model
                        st.session_state.api_configured = True
                        st.success("✅ 配置已保存")
                    else:
                        st.error("请输入 API Key")
        
        # 播客风格
        podcast_style = st.radio(
            "播客风格",
            ["single", "dialogue"],
            format_func=lambda x: "🎤 单人播客" if x == "single" else "🎭 双人对话 (小北♀ & 阿杰♂)",
            key="podcast_style_input"
        )
        
        # 语音配置（仅单人模式显示）
        if podcast_style == "single":
            voice = st.selectbox(
                "选择语音",
                ["xiaoxiao", "xiaoyi", "yunjian", "yunxi", "yunxia"],
                format_func=lambda x: {
                    "xiaoxiao": "晓晓 (女声-活泼)",
                    "xiaoyi": "晓伊 (女声-温柔)",
                    "yunjian": "云健 (男声-新闻)",
                    "yunxi": "云希 (男声-年轻)",
                    "yunxia": "云夏 (男声-讲故事)"
                }[x],
                key="voice_input"
            )
        else:
            st.info("双人对话模式将使用两种不同音色分别合成小北和阿杰的语音")
            voice = "xiaoxiao"  # 默认值
        
        resolution = st.selectbox(
            "视频分辨率",
            ["1920x1080", "1080x1920", "1280x720"],
            format_func=lambda x: {
                "1920x1080": "1920x1080 (横屏)",
                "1080x1920": "1080x1920 (竖屏-短视频)",
                "1280x720": "1280x720 (高清)"
            }[x],
            key="resolution_input"
        )
        
        target_minutes = st.slider(
            "目标时长（分钟）",
            min_value=3,
            max_value=5,
            value=4,
            step=1,
            key="target_minutes_input"
        )
        
        quality_pass = st.checkbox(
            "脚本质量优化（二次润色）",
            value=True,
            help="会额外调用一次模型，优化可读性与节奏",
            key="quality_pass_input"
        )
        
        video_motion = st.checkbox(
            "视频动效（轻微缩放 + 淡入淡出）",
            value=True,
            key="video_motion_input"
        )
        
        gen_audio = st.checkbox("生成语音", value=True, key="gen_audio_input")
        gen_video = st.checkbox("生成视频", value=True, key="gen_video_input")
        
        st.divider()
        st.markdown("### 📋 关于")
        st.markdown("""
        - 自动获取 arxiv 论文
        - AI 分析核心内容
        - 生成播客脚本
        - 语音合成
        - 视频生成
        """)
    
    # 检查 API 配置
    if not st.session_state.api_configured:
        st.warning("⚠️ 请在侧边栏输入你的 Kimi API Key 并点击保存")
        st.info("API Key 仅用于本次会话，不会存储在服务器上")
        return
    
    # 从 session state 获取配置
    api_key = st.session_state.get('api_key', '')
    base_url = st.session_state.get('base_url', 'https://api.moonshot.cn/v1')
    analyze_model = st.session_state.get('analyze_model', 'moonshot-v1-8k')
    script_model = st.session_state.get('script_model', 'moonshot-v1-8k')
    podcast_style = st.session_state.get('podcast_style_input', 'single')
    gen_audio = st.session_state.get('gen_audio_input', True)
    gen_video = st.session_state.get('gen_video_input', True)
    target_minutes = st.session_state.get('target_minutes_input', 4)
    quality_pass = st.session_state.get('quality_pass_input', True)
    video_motion = st.session_state.get('video_motion_input', True)
    
    if not api_key:
        st.error("API Key 为空，请重新保存配置")
        return
    
    # 主界面
    st.markdown('<span class="hint-badge">支持 arxiv.org/abs 或 arxiv.org/html</span>', unsafe_allow_html=True)
    url = st.text_input(
        "Arxiv 论文链接",
        placeholder="https://arxiv.org/abs/2312.03689"
    )
    
    if st.button("🚀 开始生成", type="primary", use_container_width=True):
        if not url:
            st.error("请输入论文链接")
            return
        
        arxiv_id = extract_arxiv_id(url)
        if not arxiv_id:
            st.error("无法识别 arxiv 链接格式")
            return
        
        st.success(f"识别到 arxiv ID: {arxiv_id}")
        
        # 延迟导入
        from fetcher import ArxivFetcher
        from analyzer import ContentAnalyzer
        from script_generator import PodcastScriptGenerator
        from tts_engine import TTSEngine
        from video_generator import VideoGenerator
        
        progress_bar = st.progress(0)
        status = st.empty()
        
        try:
            # 1. 获取论文
            status.info("📄 正在获取论文...")
            fetcher = ArxivFetcher()
            
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                paper_data = fetcher.fetch(url, output_dir)
                progress_bar.progress(25)
                
                # 2. 分析
                status.info("🧠 正在分析论文...")
                os.environ['ANALYZE_MODEL'] = analyze_model
                analyzer = ContentAnalyzer(api_key=api_key, base_url=base_url)
                analysis = analyzer.analyze(paper_data)
                progress_bar.progress(50)
                
                # 3. 生成脚本
                status.info("✍️ 正在生成播客脚本...")
                os.environ['SCRIPT_MODEL'] = script_model
                generator = PodcastScriptGenerator(
                    api_key=api_key, 
                    base_url=base_url,
                    style=podcast_style,
                    target_minutes=target_minutes,
                    quality_pass=quality_pass
                )
                script = generator.generate(analysis)
                progress_bar.progress(75)
                
                # 4. 生成语音
                audio_path = None
                if gen_audio:
                    status.info("🔊 正在生成语音...")
                    tts = TTSEngine(voice=voice)
                    audio_dir = output_dir / "audio"
                    audio_dir.mkdir(parents=True, exist_ok=True)
                    if podcast_style == "dialogue":
                        audio_info = tts.generate_dialogue(script.get('dialogue', []), audio_dir)
                        audio_path = audio_dir / "dialogue_merged.mp3"
                        tts.merge_dialogue_audio(audio_info.get('segments', []), audio_path)
                    else:
                        tts_text = generator.get_full_text_for_tts(script)
                        audio_path = audio_dir / "podcast.mp3"
                        tts.generate(tts_text, audio_path)
                    progress_bar.progress(85)
                
                # 5. 生成视频
                video_path = None
                if gen_video:
                    status.info("🎬 正在生成视频...")
                    # 选择图片
                    selected_images = analyzer.select_images_for_script(
                        analysis, paper_data.get('images', [])
                    )
                    
                    # 对话模式补充段落信息
                    if not script.get('segments') and script.get('dialogue'):
                        script['segments'] = _segments_from_dialogue(script['dialogue'])
                    
                    if not audio_path:
                        raise ValueError("生成视频需要先生成音频，请勾选“生成语音”。")
                    
                    if selected_images:
                        resolution_tuple = _parse_resolution(resolution)
                        video_gen = VideoGenerator(
                            resolution=resolution_tuple,
                            enable_motion=video_motion
                        )
                        video_path = output_dir / "podcast.mp4"
                        video_gen.generate(script, audio_path, selected_images, video_path)
                    else:
                        st.warning("未找到可用论文图片，将使用纯色标题卡片生成视频。")
                        resolution_tuple = _parse_resolution(resolution)
                        video_gen = VideoGenerator(
                            resolution=resolution_tuple,
                            enable_motion=video_motion
                        )
                        video_path = output_dir / "podcast.mp4"
                        video_gen.generate(script, audio_path, [], video_path)
                    progress_bar.progress(100)
                
                # 显示结果
                progress_bar.progress(100)
                status.success(f"✅ 生成完成！预计时长: {_estimate_duration_text(script)}")
                
                st.subheader("📦 结果总览")
                
                metrics = st.columns(4)
                with metrics[0]:
                    st.markdown(f"<div class='metric-card'>🕒 预计时长<br><strong>{_estimate_duration_text(script)}</strong></div>", unsafe_allow_html=True)
                with metrics[1]:
                    st.markdown(f"<div class='metric-card'>🧾 字数估计<br><strong>{_length_metric(script)}</strong></div>", unsafe_allow_html=True)
                with metrics[2]:
                    st.markdown(f"<div class='metric-card'>🖼️ 论文图片<br><strong>{len([i for i in paper_data.get('images', []) if i.get('local_path')])}</strong></div>", unsafe_allow_html=True)
                with metrics[3]:
                    st.markdown(f"<div class='metric-card'>🎭 风格<br><strong>{'双人对话' if podcast_style=='dialogue' else '单人播客'}</strong></div>", unsafe_allow_html=True)
                
                tab_script, tab_audio, tab_video, tab_analysis, tab_download = st.tabs(
                    ["📄 脚本", "🔊 音频", "🎬 视频", "📋 分析", "⬇️ 下载"]
                )
                
                with tab_script:
                    st.subheader("📄 播客脚本")
                    if podcast_style == "dialogue":
                        render_dialogue(script.get('dialogue', []))
                        with st.expander("查看纯文本版本"):
                            st.text_area("脚本内容", script['full_text'], height=300)
                    else:
                        st.text_area("脚本内容", script['full_text'], height=320)
                
                with tab_audio:
                    if audio_path and audio_path.exists():
                        st.audio(audio_path.read_bytes(), format="audio/mp3")
                        st.download_button(
                            "🎧 下载音频 (.mp3)",
                            audio_path.read_bytes(),
                            file_name=f"{arxiv_id}_podcast.mp3",
                            mime="audio/mp3",
                            use_container_width=True
                        )
                    else:
                        st.info("未生成音频。你可以在左侧勾选“生成语音”。")
                
                with tab_video:
                    if video_path and video_path.exists():
                        st.video(video_path.read_bytes())
                        st.download_button(
                            "🎬 下载视频 (.mp4)",
                            video_path.read_bytes(),
                            file_name=f"{arxiv_id}_podcast.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                    else:
                        st.info("未生成视频。你可以在左侧勾选“生成视频”。")
                
                with tab_analysis:
                    st.write(f"**核心贡献**: {analysis.get('core_contribution', '')}")
                    st.write(f"**解决的问题**: {analysis.get('problem_statement', '')}")
                    st.write(f"**方法概述**: {analysis.get('method_summary', '')}")
                    if analysis.get('key_results'):
                        st.write("**关键结果**:")
                        for result in analysis['key_results']:
                            st.write(f"  - {result}")
                
                with tab_download:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📝 下载脚本 (.txt)",
                            script['full_text'],
                            file_name=f"{arxiv_id}_script.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    with col2:
                        script_json = json.dumps(script, ensure_ascii=False, indent=2)
                        st.download_button(
                            "📊 下载结构化数据 (.json)",
                            script_json,
                            file_name=f"{arxiv_id}_script.json",
                            mime="application/json",
                            use_container_width=True
                        )
                    
                    st.download_button(
                        "📄 下载论文 HTML (.html)",
                        paper_data.get('raw_html', ''),
                        file_name=f"{arxiv_id}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                
        except Exception as e:
            st.error(f"❌ 处理失败: {str(e)}")
            progress_bar.empty()
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
