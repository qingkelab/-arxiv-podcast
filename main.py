"""
主入口模块
"""
import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入模块
from src.fetcher import ArxivFetcher
from src.analyzer import ContentAnalyzer
from src.script_generator import PodcastScriptGenerator
from src.tts_engine import TTSEngine
from src.video_generator import VideoGenerator


def process_paper(arxiv_url: str, output_base_dir: str = "output"):
    """处理单篇论文的完整流程"""
    
    print(f"\n{'='*60}")
    print(f"开始处理: {arxiv_url}")
    print(f"{'='*60}\n")
    
    # 1. 获取论文
    fetcher = ArxivFetcher()
    arxiv_id = fetcher.extract_arxiv_id(arxiv_url)
    
    output_dir = Path(output_base_dir) / arxiv_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存原始 HTML
    html_path = output_dir / "paper.html"
    if not html_path.exists():
        print("步骤 1/5: 获取论文...")
        paper_data = fetcher.fetch(arxiv_url, output_dir)
        html_path.write_text(paper_data['raw_html'], encoding='utf-8')
        print(f"  论文已保存: {html_path}")
        print(f"  标题: {paper_data['title'][:60]}...")
        print(f"  提取图片: {len([i for i in paper_data['images'] if i.get('local_path')])} 张")
    else:
        print("论文已存在，跳过获取步骤")
        # 重新解析
        paper_data = fetcher.parse_paper(html_path.read_text(encoding='utf-8'))
        paper_data['arxiv_id'] = arxiv_id
        # 加载图片信息
        images_dir = output_dir / 'images'
        if images_dir.exists():
            paper_data['images'] = [
                {'local_path': str(p), 'caption': '', 'context': ''}
                for p in images_dir.glob('*')
            ]
    
    # 2. 分析内容
    analysis_path = output_dir / "analysis.json"
    if not analysis_path.exists():
        print("\n步骤 2/5: 分析论文内容...")
        analyzer = ContentAnalyzer()
        analysis = analyzer.analyze(paper_data)
        analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"  分析完成: {analysis_path}")
        print(f"  核心贡献: {analysis.get('core_contribution', '')[:80]}...")
    else:
        print("分析结果已存在，跳过分析步骤")
        analysis = json.loads(analysis_path.read_text(encoding='utf-8'))
    
    # 3. 生成脚本
    script_path = output_dir / "script.json"
    if not script_path.exists():
        print("\n步骤 3/5: 生成播客脚本...")
        generator = PodcastScriptGenerator()
        script = generator.generate(analysis)
        script_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding='utf-8')
        
        # 同时保存纯文本版本
        text_path = output_dir / "script.txt"
        text_path.write_text(script['full_text'], encoding='utf-8')
        
        print(f"  脚本已保存: {script_path}")
        print(f"  预计时长: {script['estimated_duration_text']}")
        print(f"  总词数: {script['total_word_count']}")
        
        # 显示脚本预览
        print("\n  脚本预览:")
        for seg in script['segments'][:3]:
            print(f"    [{seg['type_name']}] {seg['text'][:50]}...")
    else:
        print("脚本已存在，跳过生成步骤")
        script = json.loads(script_path.read_text(encoding='utf-8'))
    
    # 4. 生成语音
    audio_path = output_dir / "audio.mp3"
    if not audio_path.exists():
        print("\n步骤 4/5: 生成语音...")
        tts = TTSEngine(voice='xiaoxiao')
        
        # 获取 TTS 文本
        generator = PodcastScriptGenerator()
        tts_text = generator.get_full_text_for_tts(script)
        
        tts.generate(tts_text, audio_path)
        print(f"  音频已保存: {audio_path}")
    else:
        print("音频已存在，跳过语音生成")
    
    # 5. 生成视频
    video_path = output_dir / "podcast.mp4"
    if not video_path.exists():
        print("\n步骤 5/5: 生成视频...")
        
        # 选择图片
        analyzer = ContentAnalyzer()
        selected_images = analyzer.select_images_for_script(analysis, paper_data.get('images', []))
        print(f"  选用图片: {len(selected_images)} 张")
        
        if selected_images:
            generator = VideoGenerator(resolution=(1920, 1080))
            generator.generate(script, audio_path, selected_images, video_path)
            print(f"\n✅ 视频播客已生成: {video_path}")
        else:
            print("  警告: 没有可用图片，跳过视频生成")
    else:
        print("视频已存在，跳过视频生成")
    
    print(f"\n{'='*60}")
    print(f"处理完成! 输出目录: {output_dir}")
    print(f"{'='*60}\n")
    
    return output_dir


def main():
    parser = argparse.ArgumentParser(description='Arxiv Paper to Video Podcast')
    parser.add_argument('url', help='Arxiv paper URL')
    parser.add_argument('-o', '--output', default='output', help='Output directory')
    
    args = parser.parse_args()
    
    # 检查 API key
    if not os.getenv('OPENAI_API_KEY'):
        print("错误: 请设置 OPENAI_API_KEY 环境变量或在 .env 文件中配置")
        print("复制 .env.example 为 .env 并填入你的 API Key")
        sys.exit(1)
    
    try:
        process_paper(args.url, args.output)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
