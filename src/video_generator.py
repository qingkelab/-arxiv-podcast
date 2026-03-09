"""
视频生成模块
"""
import os
from pathlib import Path
from typing import List, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont
# import numpy as np  # 可选依赖


class VideoGenerator:
    """生成视频播客"""
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080)):
        self.resolution = resolution
        self.width, self.height = resolution
        self.fps = 30
    
    def generate(
        self,
        script: dict,
        audio_path: Path,
        images: List[Dict],
        output_path: Path
    ) -> Path:
        """生成完整视频"""
        
        print("正在生成视频...")
        
        # 准备图片素材
        prepared_images = self._prepare_images(images, script)
        
        # 使用 moviepy 生成视频
        try:
            from moviepy.editor import (
                AudioFileClip, ImageClip, CompositeVideoClip,
                concatenate_videoclips, TextClip
            )
            
            # 加载音频
            audio = AudioFileClip(str(audio_path))
            audio_duration = audio.duration
            
            # 创建视频片段
            video_clips = []
            
            # 根据脚本段落分配图片
            segments = script.get('segments', [])
            segment_duration = audio_duration / len(segments) if segments else audio_duration
            
            for i, segment in enumerate(segments):
                # 选择图片
                img_path = self._select_image_for_segment(segment, prepared_images, i)
                
                # 创建图片片段
                if img_path and Path(img_path).exists():
                    clip = self._create_image_clip(
                        img_path, 
                        segment_duration,
                        segment
                    )
                else:
                    # 使用标题卡片
                    clip = self._create_title_card(
                        segment,
                        segment_duration
                    )
                
                video_clips.append(clip)
            
            # 合并视频
            final_video = concatenate_videoclips(video_clips, method="compose")
            final_video = final_video.set_audio(audio)
            
            # 输出
            output_path.parent.mkdir(parents=True, exist_ok=True)
            final_video.write_videofile(
                str(output_path),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=str(output_path.with_suffix('.tmp.m4a')),
                remove_temp=True
            )
            
            # 清理
            audio.close()
            for clip in video_clips:
                clip.close()
            final_video.close()
            
            print(f"视频已生成: {output_path}")
            return output_path
            
        except ImportError:
            print("moviepy 未安装，使用 ffmpeg 直接合成...")
            return self._generate_with_ffmpeg(
                script, audio_path, prepared_images, output_path
            )
    
    def _prepare_images(self, images: List[Dict], script: dict) -> List[Dict]:
        """准备图片素材（调整尺寸、添加效果）"""
        prepared = []
        
        for img_info in images:
            img_path = img_info.get('path')
            if not img_path or not Path(img_path).exists():
                continue
            
            try:
                # 打开图片
                img = Image.open(img_path)
                
                # 转换为 RGB（处理RGBA）
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # 调整尺寸（保持比例，填充背景）
                img = self._resize_with_padding(img)
                
                prepared.append({
                    'original_path': img_path,
                    'pil_image': img,
                    'use_for': img_info.get('use_for', 'general'),
                    'caption': img_info.get('caption', '')
                })
                
            except Exception as e:
                print(f"  处理图片失败 {img_path}: {e}")
                continue
        
        return prepared
    
    def _resize_with_padding(self, img: Image.Image) -> Image.Image:
        """调整图片尺寸，保持比例，黑色填充"""
        target_ratio = self.width / self.height
        img_ratio = img.width / img.height
        
        if img_ratio > target_ratio:
            # 图片更宽，按宽度缩放
            new_width = self.width
            new_height = int(self.width / img_ratio)
        else:
            # 图片更高，按高度缩放
            new_height = self.height
            new_width = int(self.height * img_ratio)
        
        # 缩放
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 创建背景
        background = Image.new('RGB', (self.width, self.height), (20, 20, 20))
        
        # 居中粘贴
        paste_x = (self.width - new_width) // 2
        paste_y = (self.height - new_height) // 2
        background.paste(img, (paste_x, paste_y))
        
        return background
    
    def _select_image_for_segment(self, segment: dict, images: List[Dict], index: int) -> str:
        """为段落选择合适的图片"""
        seg_type = segment.get('type', 'general')
        
        # 根据段落类型选择
        for img in images:
            if img.get('use_for') == seg_type:
                return img.get('original_path')
        
        # 按索引循环使用
        if images:
            return images[index % len(images)].get('original_path')
        
        return None
    
    def _create_image_clip(self, img_path: str, duration: float, segment: dict):
        """创建图片视频片段（使用 moviepy）"""
        from moviepy.editor import ImageClip
        
        # 打开并调整图片
        img = Image.open(img_path)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img = self._resize_with_padding(img)
        
        # 保存临时文件
        temp_path = Path(img_path).parent / f"temp_{segment.get('type', 'frame')}.jpg"
        img.save(temp_path, quality=95)
        
        clip = ImageClip(str(temp_path), duration=duration)
        
        # 添加 Ken Burns 效果（缓慢缩放）
        # 简单实现：轻微放大
        
        return clip
    
    def _create_title_card(self, segment: dict, duration: float):
        """创建标题卡片"""
        from moviepy.editor import ImageClip
        
        # 创建纯色背景
        img = Image.new('RGB', self.resolution, (30, 30, 40))
        draw = ImageDraw.Draw(img)
        
        # 添加文字
        title = segment.get('type_name', 'Section')
        text = segment.get('text', '')[:100] + '...'
        
        # 尝试添加文字（如果没有字体，就只用背景）
        try:
            # 使用默认字体
            from PIL import ImageFont
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # 绘制标题
            bbox = draw.textbbox((0, 0), title, font=font_large)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, self.height // 3), title, fill=(255, 255, 255), font=font_large)
            
        except Exception as e:
            print(f"  文字渲染失败: {e}")
        
        # 保存临时图片
        temp_path = Path(f"/tmp/title_card_{segment.get('type', 'frame')}.jpg")
        img.save(temp_path)
        
        return ImageClip(str(temp_path), duration=duration)
    
    def _generate_with_ffmpeg(
        self,
        script: dict,
        audio_path: Path,
        images: List[Dict],
        output_path: Path
    ) -> Path:
        """使用 ffmpeg 直接生成视频（备用方案）"""
        
        import subprocess
        import tempfile
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # 准备帧
            frame_list = []
            
            # 获取音频时长
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)],
                capture_output=True, text=True
            )
            audio_duration = float(result.stdout.strip())
            
            # 为每个段落生成帧
            segments = script.get('segments', [])
            segment_duration = audio_duration / len(segments) if segments else audio_duration
            frames_per_segment = int(segment_duration * self.fps)
            
            frame_idx = 0
            for i, segment in enumerate(segments):
                # 选择或创建图片
                img = self._get_or_create_frame(segment, images, i)
                
                # 复制帧
                for _ in range(frames_per_segment):
                    frame_path = tmpdir / f"frame_{frame_idx:06d}.jpg"
                    img.save(frame_path, quality=95)
                    frame_list.append(frame_path)
                    frame_idx += 1
            
            # 使用 ffmpeg 合成视频
            cmd = [
                'ffmpeg', '-y',
                '-framerate', str(self.fps),
                '-i', str(tmpdir / 'frame_%06d.jpg'),
                '-i', str(audio_path),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac',
                '-shortest',
                str(output_path)
            ]
            
            print(f"运行: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
        
        print(f"视频已生成: {output_path}")
        return output_path
    
    def _get_or_create_frame(self, segment: dict, images: List[Dict], index: int) -> Image.Image:
        """获取或创建帧图片"""
        seg_type = segment.get('type', 'general')
        
        # 尝试找到匹配的图片
        for img in images:
            if img.get('use_for') == seg_type:
                return img.get('pil_image')
        
        # 按索引使用
        if images:
            return images[index % len(images)].get('pil_image')
        
        # 创建默认帧
        return Image.new('RGB', self.resolution, (30, 30, 40))
