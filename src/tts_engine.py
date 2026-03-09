"""
TTS 语音合成模块
"""
import asyncio
import edge_tts
from pathlib import Path
from typing import Optional


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
    
    # 英文语音
    ENGLISH_VOICES = {
        'jenny': 'en-US-JennyNeural',
        'guy': 'en-US-GuyNeural',
    }
    
    def __init__(self, voice: str = 'xiaoxiao'):
        self.voice = self.CHINESE_VOICES.get(voice, self.CHINESE_VOICES['xiaoxiao'])
        self.rate = "+0%"  # 语速
        self.volume = "+0%"  # 音量
    
    async def _generate_async(self, text: str, output_path: Path) -> Path:
        """异步生成音频"""
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume
        )
        await communicate.save(str(output_path))
        return output_path
    
    def generate(self, text: str, output_path: Path) -> Path:
        """生成 TTS 音频"""
        print(f"正在生成语音... (使用 {self.voice})")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # edge-tts 需要异步运行
        asyncio.run(self._generate_async(text, output_path))
        
        print(f"语音已保存: {output_path}")
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
