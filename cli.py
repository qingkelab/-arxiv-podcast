"""
增强版 CLI 模块 - 带进度条和交互式界面
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich import box
from dotenv import load_dotenv

from fetcher import ArxivFetcher
from analyzer import ContentAnalyzer
from script_generator import PodcastScriptGenerator
from tts_engine import TTSEngine
from video_generator import VideoGenerator

load_dotenv()
console = Console()


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    arxiv_id: str
    output_dir: Path
    files: dict
    duration: float
    error: Optional[str] = None


class ArxivPodcastCLI:
    """交互式命令行界面"""
    
    def __init__(self):
        self.console = Console()
        
    def print_banner(self):
        """打印欢迎横幅"""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🎙️  Arxiv Paper to Video Podcast Generator              ║
║                                                           ║
║   将学术论文转换为 3-5 分钟视频播客                        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """
        self.console.print(Panel(banner, border_style="blue", box=box.DOUBLE))
    
    def print_config(self):
        """打印当前配置"""
        table = Table(title="⚙️ 当前配置", box=box.ROUNDED)
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")
        
        table.add_row("API Key", "✓ 已配置" if os.getenv('OPENAI_API_KEY') else "✗ 未配置")
        table.add_row("输出目录", "output/")
        table.add_row("默认语音", "晓晓 (女声)")
        table.add_row("视频分辨率", "1920x1080")
        
        self.console.print(table)
        self.console.print()
    
    def process_with_progress(
        self,
        url: str,
        voice: str = "xiaoxiao",
        resolution: tuple = (1920, 1080),
        skip_video: bool = False
    ) -> ProcessingResult:
        """带进度显示的处理流程"""
        
        start_time = time.time()
        files = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            try:
                # 初始化
                fetcher = ArxivFetcher()
                arxiv_id = fetcher.extract_arxiv_id(url)
                output_dir = Path("output") / arxiv_id
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # 任务 1: 获取论文
                task1 = progress.add_task("[cyan]📄 获取论文...", total=100)
                paper_data = fetcher.fetch(url, output_dir)
                
                html_path = output_dir / "paper.html"
                html_path.write_text(paper_data['raw_html'], encoding='utf-8')
                files['html'] = html_path
                
                image_count = len([i for i in paper_data['images'] if i.get('local_path')])
                progress.update(task1, completed=100, description=f"[green]📄 论文获取完成 ({image_count} 张图片)")
                
                # 任务 2: 分析内容
                task2 = progress.add_task("[cyan]🧠 分析论文内容...", total=100)
                analyzer = ContentAnalyzer()
                analysis = analyzer.analyze(paper_data)
                
                analysis_path = output_dir / "analysis.json"
                analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding='utf-8')
                files['analysis'] = analysis_path
                
                progress.update(task2, completed=100, 
                              description=f"[green]🧠 分析完成: {analysis.get('core_contribution', '')[:40]}...")
                
                # 任务 3: 生成脚本
                task3 = progress.add_task("[cyan]✍️ 生成播客脚本...", total=100)
                script_gen = PodcastScriptGenerator()
                script = script_gen.generate(analysis)
                
                script_path = output_dir / "script.json"
                script_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding='utf-8')
                files['script_json'] = script_path
                
                text_path = output_dir / "script.txt"
                text_path.write_text(script['full_text'], encoding='utf-8')
                files['script_txt'] = text_path
                
                progress.update(task3, completed=100,
                              description=f"[green]✍️ 脚本完成 ({script['estimated_duration_text']}, {script['total_word_count']} 词)")
                
                # 任务 4: 生成语音
                task4 = progress.add_task("[cyan]🔊 合成语音...", total=100)
                tts = TTSEngine(voice=voice)
                tts_text = script_gen.get_full_text_for_tts(script)
                
                audio_path = output_dir / "audio.mp3"
                tts.generate(tts_text, audio_path)
                files['audio'] = audio_path
                
                progress.update(task4, completed=100, description="[green]🔊 语音合成完成")
                
                # 任务 5: 生成视频
                if not skip_video:
                    task5 = progress.add_task("[cyan]🎬 生成视频...", total=100)
                    
                    selected_images = analyzer.select_images_for_script(
                        analysis, paper_data.get('images', [])
                    )
                    
                    if selected_images:
                        video_gen = VideoGenerator(resolution=resolution)
                        video_path = output_dir / "podcast.mp4"
                        video_gen.generate(script, audio_path, selected_images, video_path)
                        files['video'] = video_path
                        
                        progress.update(task5, completed=100, description="[green]🎬 视频生成完成")
                    else:
                        progress.update(task5, completed=100, description="[yellow]⚠️ 无可用图片，跳过视频")
                
                duration = time.time() - start_time
                
                return ProcessingResult(
                    success=True,
                    arxiv_id=arxiv_id,
                    output_dir=output_dir,
                    files=files,
                    duration=duration
                )
                
            except Exception as e:
                import traceback
                return ProcessingResult(
                    success=False,
                    arxiv_id=arxiv_id if 'arxiv_id' in locals() else "unknown",
                    output_dir=output_dir if 'output_dir' in locals() else Path("output"),
                    files=files,
                    duration=time.time() - start_time,
                    error=f"{str(e)}\n{traceback.format_exc()}"
                )
    
    def print_result(self, result: ProcessingResult):
        """打印处理结果"""
        if result.success:
            self.console.print()
            self.console.print(Panel(
                f"[bold green]✅ 处理成功！[/bold green]\n\n"
                f"📄 Arxiv ID: [cyan]{result.arxiv_id}[/cyan]\n"
                f"⏱️  耗时: [yellow]{result.duration:.1f}[/yellow] 秒\n"
                f"📁 输出目录: [blue]{result.output_dir}[/blue]",
                title="处理结果",
                border_style="green"
            ))
            
            # 文件列表
            table = Table(title="📦 生成的文件", box=box.ROUNDED)
            table.add_column("类型", style="cyan")
            table.add_column("文件", style="green")
            
            if 'html' in result.files:
                table.add_row("📄 原始论文", str(result.files['html'].name))
            if 'analysis' in result.files:
                table.add_row("🧠 分析报告", str(result.files['analysis'].name))
            if 'script_txt' in result.files:
                table.add_row("📝 播客脚本", str(result.files['script_txt'].name))
            if 'audio' in result.files:
                table.add_row("🔊 音频文件", str(result.files['audio'].name))
            if 'video' in result.files:
                table.add_row("🎬 视频播客", str(result.files['video'].name))
            
            self.console.print(table)
            
            # 提示下一步
            self.console.print()
            self.console.print(Panel(
                "[dim]提示:[/dim]\n"
                f"  • 查看脚本: [bold]cat {result.output_dir}/script.txt[/bold]\n"
                f"  • 播放音频: [bold]ffplay {result.output_dir}/audio.mp3[/bold]\n"
                f"  • 观看视频: [bold]ffplay {result.output_dir}/podcast.mp4[/bold]",
                border_style="dim"
            ))
            
        else:
            self.console.print()
            self.console.print(Panel(
                f"[bold red]❌ 处理失败[/bold red]\n\n"
                f"📄 Arxiv ID: [cyan]{result.arxiv_id}[/cyan]\n"
                f"⏱️  耗时: [yellow]{result.duration:.1f}[/yellow] 秒\n\n"
                f"[red]{result.error}[/red]",
                title="错误信息",
                border_style="red"
            ))
    
    def interactive_mode(self):
        """交互式模式"""
        self.print_banner()
        self.print_config()
        
        # 检查 API Key
        if not os.getenv('OPENAI_API_KEY'):
            self.console.print("[red]错误: 未设置 OPENAI_API_KEY 环境变量[/red]")
            self.console.print("请在 .env 文件中配置或设置环境变量")
            return
        
        # 输入 arxiv URL
        self.console.print("[bold]请输入 Arxiv 论文链接:[/bold]")
        self.console.print("[dim]示例: https://arxiv.org/abs/2312.03689[/dim]")
        url = input("> ").strip()
        
        if not url:
            self.console.print("[red]未输入链接，退出[/red]")
            return
        
        # 选择语音
        self.console.print()
        self.console.print("[bold]选择语音:[/bold]")
        voices = {
            "1": ("xiaoxiao", "晓晓 - 女声(活泼)"),
            "2": ("xiaoyi", "晓伊 - 女声(温柔)"),
            "3": ("yunjian", "云健 - 男声(新闻)"),
            "4": ("yunxi", "云希 - 男声(年轻)"),
            "5": ("yunxia", "云夏 - 男声(讲故事)")
        }
        for k, (_, name) in voices.items():
            self.console.print(f"  {k}. {name}")
        
        voice_choice = input("选择 (1-5, 默认1): ").strip() or "1"
        voice = voices.get(voice_choice, voices["1"])[0]
        
        # 选择分辨率
        self.console.print()
        self.console.print("[bold]选择视频分辨率:[/bold]")
        resolutions = {
            "1": ((1920, 1080), "1920x1080 - 横屏(推荐)"),
            "2": ((1080, 1920), "1080x1920 - 竖屏(短视频)"),
            "3": ((1280, 720), "1280x720 - 高清")
        }
        for k, (_, name) in resolutions.items():
            self.console.print(f"  {k}. {name}")
        
        res_choice = input("选择 (1-3, 默认1): ").strip() or "1"
        resolution = resolutions.get(res_choice, resolutions["1"])[0]
        
        # 确认
        self.console.print()
        self.console.print(Panel(
            f"URL: [cyan]{url}[/cyan]\n"
            f"语音: [green]{voices[voice_choice][1]}[/green]\n"
            f"分辨率: [green]{resolutions[res_choice][1]}[/green]",
            title="确认配置"
        ))
        
        confirm = input("确认开始? (Y/n): ").strip().lower()
        if confirm not in ('', 'y', 'yes'):
            self.console.print("[yellow]已取消[/yellow]")
            return
        
        # 开始处理
        self.console.print()
        result = self.process_with_progress(url, voice, resolution)
        self.print_result(result)


def main():
    parser = argparse.ArgumentParser(
        description='Arxiv Paper to Video Podcast - 增强版 CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 交互式模式
  %(prog)s -u https://arxiv.org/abs/2312.03689
  %(prog)s -u https://arxiv.org/abs/2312.03689 -v xiaoxiao -r 1080x1920
  %(prog)s -u URL --skip-video  # 只生成音频
        """
    )
    
    parser.add_argument('-u', '--url', help='Arxiv 论文链接')
    parser.add_argument('-v', '--voice', default='xiaoxiao',
                       choices=['xiaoxiao', 'xiaoyi', 'yunjian', 'yunxi', 'yunxia'],
                       help='语音选择 (默认: xiaoxiao)')
    parser.add_argument('-r', '--resolution', default='1920x1080',
                       choices=['1920x1080', '1080x1920', '1280x720'],
                       help='视频分辨率 (默认: 1920x1080)')
    parser.add_argument('--skip-video', action='store_true',
                       help='跳过视频生成，只生成音频')
    parser.add_argument('--web', action='store_true',
                       help='启动 Web 服务')
    parser.add_argument('-o', '--output', default='output', help='输出目录')
    
    args = parser.parse_args()
    
    # 启动 Web 服务
    if args.web:
        from web_server import main as web_main
        web_main()
        return
    
    cli = ArxivPodcastCLI()
    
    # 交互式模式
    if not args.url:
        cli.interactive_mode()
        return
    
    # 命令行模式
    cli.print_banner()
    
    # 检查 API Key
    if not os.getenv('OPENAI_API_KEY'):
        cli.console.print("[red]错误: 未设置 OPENAI_API_KEY 环境变量[/red]")
        sys.exit(1)
    
    # 解析分辨率
    res_map = {
        '1920x1080': (1920, 1080),
        '1080x1920': (1080, 1920),
        '1280x720': (1280, 720)
    }
    resolution = res_map[args.resolution]
    
    # 处理
    result = cli.process_with_progress(
        args.url, 
        args.voice, 
        resolution,
        skip_video=args.skip_video
    )
    cli.print_result(result)
    
    sys.exit(0 if result.success else 1)


if __name__ == '__main__':
    main()
