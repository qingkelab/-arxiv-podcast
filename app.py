"""
Streamlit 优化版 - 轻量级，适合 Cloud 部署
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


def main():
    # 标题
    st.markdown('<h1 class="main-header">🎙️ Arxiv Podcast</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">将学术论文转换为 3-5 分钟播客</p>', unsafe_allow_html=True)
    
    # 检查 API Key
    if not os.getenv('OPENAI_API_KEY'):
        st.error("⚠️ 未设置 OPENAI_API_KEY")
        st.info("请在 Streamlit Secrets 中配置 API Key")
        return
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 配置")
        
        voice = st.selectbox(
            "选择语音",
            ["xiaoxiao", "xiaoyi", "yunjian", "yunxi", "yunxia"],
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
            ["1920x1080", "1080x1920", "1280x720"],
            format_func=lambda x: {
                "1920x1080": "1920x1080 (横屏)",
                "1080x1920": "1080x1920 (竖屏-短视频)",
                "1280x720": "1280x720 (高清)"
            }[x]
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
                progress_bar.progress(20)
                
                # 2. 分析
                status.info("🧠 正在分析论文...")
                analyzer = ContentAnalyzer()
                analysis = analyzer.analyze(paper_data)
                progress_bar.progress(40)
                
                # 3. 生成脚本
                status.info("✍️ 正在生成脚本...")
                generator = PodcastScriptGenerator()
                script = generator.generate(analysis)
                progress_bar.progress(60)
                
                # 显示结果
                progress_bar.progress(100)
                status.success("✅ 生成完成！")
                
                # 显示脚本
                st.subheader("📄 播客脚本")
                st.text_area("脚本内容", script['full_text'], height=300)
                
                # 下载按钮
                st.download_button(
                    "📝 下载脚本",
                    script['full_text'],
                    file_name=f"{arxiv_id}_script.txt",
                    mime="text/plain"
                )
                
        except Exception as e:
            st.error(f"❌ 处理失败: {str(e)}")
            progress_bar.empty()


if __name__ == "__main__":
    main()
