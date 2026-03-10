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
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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


def main():
    # 标题
    st.markdown('<h1 class="main-header">🎙️ Arxiv Podcast</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">将学术论文转换为 3-5 分钟播客</p>', unsafe_allow_html=True)
    
    # 初始化 session state
    if 'api_configured' not in st.session_state:
        st.session_state.api_configured = False
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        
        # API 配置
        with st.expander("🔑 API 配置", expanded=True):
            api_key = st.text_input(
                "Kimi API Key",
                type="password",
                placeholder="sk-...",
                help="你的 Kimi API Key，不会存储在服务器上",
                key="api_key_input"
            )
            
            base_url = st.text_input(
                "API Base URL",
                value="https://api.moonshot.cn/v1",
                help="Kimi API 地址",
                key="base_url_input"
            )
            
            analyze_model = st.selectbox(
                "分析模型",
                ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
                index=0,
                help="用于分析论文的模型",
                key="analyze_model_input"
            )
            
            script_model = st.selectbox(
                "脚本生成模型",
                ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
                index=0,
                help="用于生成播客脚本的模型",
                key="script_model_input"
            )
            
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
    
    # 调试信息（临时）
    st.write(f"Debug: API Key 前15位: {api_key[:15] if api_key else 'None'}...")
    st.write(f"Debug: Base URL: {base_url}")
    st.write(f"Debug: 分析模型: {analyze_model}")
    
    if not api_key:
        st.error("API Key 为空，请重新保存配置")
        return
    
    # 主界面
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
                st.write(f"Debug: 传入 analyzer 的 API Key 前10位: {api_key[:10] if api_key else 'None'}...")
                analyzer = ContentAnalyzer(api_key=api_key, base_url=base_url)
                analysis = analyzer.analyze(paper_data)
                progress_bar.progress(50)
                
                # 3. 生成脚本
                status.info("✍️ 正在生成播客脚本...")
                generator = PodcastScriptGenerator(
                    api_key=api_key, 
                    base_url=base_url,
                    style=podcast_style
                )
                script = generator.generate(analysis)
                progress_bar.progress(75)
                
                # 显示结果
                progress_bar.progress(100)
                status.success(f"✅ 生成完成！预计时长: {script.get('estimated_duration_text', '未知')}")
                
                # 根据风格显示脚本
                st.subheader("📄 播客脚本")
                
                if podcast_style == "dialogue":
                    # 显示双人对话
                    render_dialogue(script.get('dialogue', []))
                    
                    # 显示纯文本版本
                    with st.expander("查看纯文本版本"):
                        st.text_area("脚本内容", script['full_text'], height=300)
                else:
                    # 显示单人播客
                    st.text_area("脚本内容", script['full_text'], height=300)
                
                # 下载按钮
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
                    # JSON 格式下载
                    script_json = json.dumps(script, ensure_ascii=False, indent=2)
                    st.download_button(
                        "📊 下载结构化数据 (.json)",
                        script_json,
                        file_name=f"{arxiv_id}_script.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                # 显示分析摘要
                with st.expander("📋 论文分析摘要"):
                    st.write(f"**核心贡献**: {analysis.get('core_contribution', '')}")
                    st.write(f"**解决的问题**: {analysis.get('problem_statement', '')}")
                    st.write(f"**方法概述**: {analysis.get('method_summary', '')}")
                    if analysis.get('key_results'):
                        st.write("**关键结果**:")
                        for result in analysis['key_results']:
                            st.write(f"  - {result}")
                
        except Exception as e:
            st.error(f"❌ 处理失败: {str(e)}")
            progress_bar.empty()
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
