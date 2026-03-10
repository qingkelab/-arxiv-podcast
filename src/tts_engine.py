"""
TTS 语音合成模块
支持单人播客和双人对话模式
"""
import asyncio
import edge_tts
from pathlib import Path
from typing import Optional, Dict, List


class TTSEngine:
    """使用 edge-tts 进行语音合成"""
    
    # 可用的中文语音
    CHINESE_VOICES = {
        'xiaoxiao': 'zh-CN-XiaoxiaoNeural',      # 女声，活泼
        'xiaoyi': 'zh-CN-XiaoyiNeural',          # 女声，温柔
        'yunjian': 'zh-CN-YunjianNeural',        # 男声，新闻
        'yunxi': 'zh-CN-YunxiNeural',            # 男声，年轻
        'yunxia': 'zh-CN-YunxiaNeural',          # 男声，讲故事
    }
    
    # 双人对话默认配置（一男一女）
    DIALOGUE_VOICES = {
        'xiaobei': 'zh-CN-XiaoxiaoNeural',   # 小北(女) - 女声活泼
        'ajie': 'zh-CN-YunxiaNeural',        # 阿杰(男) - 男声讲故事
    }
    
    def __init__(self, voice: str = 'xiaoxiao'):
        self.voice = self.CHINESE_VOICES.get(voice, self.CHINESE_VOICES['xiaoxiao'])
        self.rate = "+0%"  # 语速
        self.volume = "+0%"  # 音量
    
    async def _generate_async(self, text: str, output_path: Path, voice: str = None) -> Path:
        """异步生成音频"""
        use_voice = voice or self.voice
        communicate = edge_tts.Communicate(
            text=text,
            voice=use_voice,
            rate=self.rate,
            volume=self.volume
        )
        await communicate.save(str(output_path))
        return output_path
    
    def generate(self, text: str, output_path: Path, voice: str = None) -> Path:
        """生成 TTS 音频"""
        print(f"正在生成语音... (使用 {voice or self.voice})")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # edge-tts 需要异步运行
        asyncio.run(self._generate_async(text, output_path, voice))
        
        print(f"语音已保存: {output_path}")
        return output_path
    
    def generate_dialogue(self, dialogue: List[Dict], output_dir: Path) -> Dict:
        """为双人对话生成音频（每个说话人单独合成后合并）"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        audio_segments = []
        
        for i, line in enumerate(dialogue):
            speaker = line['speaker']
            text = line['text']
            
            # 清理文本（移除括号内的动作提示）
            import re
            clean_text = re.sub(r'[（(].*?[）)]', '', text).strip()
            if not clean_text:
                continue
            
            # 选择对应音色
            voice = self.DIALOGUE_VOICES.get(speaker, self.CHINESE_VOICES['xiaoxiao'])
            
            output_path = output_dir / f"dialogue_{i:03d}_{speaker}.mp3"
            
            print(f"  生成对话 {i+1}/{len(dialogue)}: {speaker}")
            self.generate(clean_text, output_path, voice)
            
            # 获取音频时长
            duration = self._get_audio_duration(output_path)
            
            audio_segments.append({
                'speaker': speaker,
                'path': str(output_path),
                'duration': duration,
                'text': clean_text[:100] + '...' if len(clean_text) > 100 else clean_text
            })
        
        return {
            'segments': audio_segments,
            'total_duration': sum(s['duration'] for s in audio_segments)
        }
    
    def merge_dialogue_audio(self, audio_segments: List[Dict], output_path: Path) -> Path:
        """合并对话音频片段为单个文件"""
        try:
            from pydub import AudioSegment
            
            combined = AudioSegment.empty()
            
            for seg in audio_segments:
                audio = AudioSegment.from_mp3(seg['path'])
                combined += audio
                # 添加短暂停顿（0.3秒）
                combined += AudioSegment.silent(duration=300)
            
            combined.export(output_path, format="mp3")
            print(f"合并音频已保存: {output_path}")
            return output_path
            
        except ImportError:
            # 使用 ffmpeg 合并
            import subprocess
            import tempfile
            
            # 创建文件列表
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for seg in audio_segments:
                    f.write(f"file '{seg['path']}'\n")
                list_file = f.name
            
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', list_file,
                '-c', 'copy',
                str(output_path)
            ]
            
            subprocess.run(cmd, check=True)
            Path(list_file).unlink()
            
            print(f"合并音频已保存: {output_path}")
            return output_path
    
    def generate_with_segments(self, script: dict, output_dir: Path) -> dict:
        """为每个段落生成单独的音频（用于精细控制）"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        audio_segments = []
        
        for i, segment in enumerate(script.get('segments', [])):
            text = segment['text']
            # 清理文本
            import re
            text = re.sub(r'\[.*?\]', '', text)  # 移除标记
            
            output_path = output_dir / f"segment_{i:02d}_{segment['type']}.mp3"
            
            print(f"  生成段落 {i+1}/{len(script.get('segments', []))}: {segment['type_name']}")
            self.generate(text, output_path)
            
            # 获取音频时长
            duration = self._get_audio_duration(output_path)
            
            audio_segments.append({
                'type': segment['type'],
                'path': str(output_path),
                'duration': duration,
                'text': text[:100] + '...' if len(text) > 100 else text
            })
        
        return {
            'segments': audio_segments,
            'total_duration': sum(s['duration'] for s in audio_segments)
        }
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """获取音频时长（秒）"""
        try:
            from mutagen.mp3 import MP3
            audio = MP3(str(audio_path))
            return audio.info.length
        except:
            # 估算：约 150 词/分钟
            return 0.0
