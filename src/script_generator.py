"""
播客脚本生成模块
"""
import json
from typing import Dict, List
from openai import OpenAI
import os


class PodcastScriptGenerator:
    """生成 3-5 分钟的播客脚本"""
    
    def __init__(self, api_key: str = None, base_url: str = None, style: str = "single"):
        self.client = OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY'),
            base_url=base_url or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        )
        self.model = os.getenv('SCRIPT_MODEL', 'kimi-k2-0711-preview')
        self.style = style  # "single" 单人或 "dialogue" 双人对话
        
        # 语速: 约 150 词/分钟
        # 3-5 分钟 = 450-750 词
        self.target_word_count = 600
        self.words_per_minute = 150
    
    def generate(self, analysis: Dict) -> Dict:
        """生成完整播客脚本"""
        
        if self.style == "dialogue":
            return self._generate_dialogue(analysis)
        else:
            return self._generate_single(analysis)
    
    def _generate_single(self, analysis: Dict) -> Dict:
        """生成单人播客脚本"""
        
        prompt = self._build_script_prompt(analysis)
        
        print("正在生成单人播客脚本...")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": """你是一位专业的科技播客撰稿人。你的脚本风格：
- 口语化、自然，像朋友聊天
- 用类比解释复杂概念
- 有节奏感，适当的停顿和强调
- 开头抓人，结尾有力
- 总时长控制在 3-5 分钟（约 600 词）"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,
            max_tokens=2500
        )
        
        script_text = response.choices[0].message.content
        script = self._parse_script(script_text, analysis)
        script['style'] = 'single'
        return script
    
    def _generate_dialogue(self, analysis: Dict) -> Dict:
        """生成双人对话播客脚本"""
        
        prompt = self._build_dialogue_prompt(analysis)
        
        print("正在生成双人对话播客脚本...")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": """你是一位专业的科技播客编剧。你创作的双人对话播客风格：
- 主持人(小北)和嘉宾(阿杰)的对话形式
- 小北负责引导话题、提问、总结，语气活泼亲和
- 阿杰负责深度解读、技术分析、补充细节，语气沉稳专业
- 两人有自然的互动、插话、呼应、玩笑
- 用类比和例子解释复杂概念
- 避免照本宣科，像朋友间的真实对话
- 总时长控制在 3-5 分钟（约 600-800 词）"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.85,
            max_tokens=3000
        )
        
        script_text = response.choices[0].message.content
        script = self._parse_dialogue_script(script_text, analysis)
        script['style'] = 'dialogue'
        return script
    
    def _build_dialogue_prompt(self, analysis: Dict) -> str:
        """构建双人对话脚本生成提示"""
        
        return f"""请为以下学术论文撰写一个 3-5 分钟的双人对话科普播客脚本。

论文信息:
- 标题: {analysis.get('title', '')}
- 核心贡献: {analysis.get('core_contribution', '')}
- 解决的问题: {analysis.get('problem_statement', '')}
- 方法概述: {analysis.get('method_summary', '')}
- 关键结果: {', '.join(analysis.get('key_results', []))}
- 意义: {analysis.get('significance', '')}
- 有趣之处: {', '.join(analysis.get('interesting_aspects', []))}

人物设定:
- 小北(主持人，女): 科技爱好者，好奇心强，善于提问，语气活泼亲和，代表普通听众视角
- 阿杰(嘉宾，男): AI研究员，专业背景，善于深入浅出解释技术，语气沉稳但有温度

技术要求:
- 总字数: 约 600-800 词（3-5 分钟）
- 语速: 正常对话速度，两人交替自然
- 风格: 轻松、有趣、易懂，像朋友聊天

脚本结构:
1. **开场** (约 100-120 词):
   - 小北打招呼，引入今天的论文话题
   - 阿杰回应，简单预告今天要聊的内容
   - 制造一点期待感

2. **问题背景** (约 150-180 词):
   - 小北提出"这个问题为什么重要？"
   - 阿杰用通俗语言解释背景和现有挑战
   - 小北适时插话表示理解或惊讶

3. **方法介绍** (约 180-220 词):
   - 小北问"他们是怎么解决的？"
   - 阿杰解释核心创新，用类比让概念易懂
   - 两人互动，小北追问细节，阿杰补充
   - 避免过多术语，必要时阿杰会解释

4. **结果与意义** (约 150-180 词):
   - 小北问"效果怎么样？"
   - 阿杰分享关键成果和影响
   - 小北联系实际应用场景
   - 阿杰展望未来或补充思考

5. **结尾** (约 80-100 词):
   - 小北总结要点
   - 阿杰补充一句金句或展望
   - 自然的结束语，可以有点幽默

格式要求:
- 每行以 "小北:" 或 "阿杰:" 开头
- 对话自然，有打断、呼应、笑声等真实感
- 可以在括号里加动作或语气提示，如 (笑)、(思考)
- 避免长篇大论，每人每次说话控制在2-3句话

请直接输出对话脚本。"""
    
    def _build_script_prompt(self, analysis: Dict) -> str:
        """构建脚本生成提示"""
        
        return f"""请为以下学术论文撰写一个 3-5 分钟的科普播客脚本。

论文信息:
- 标题: {analysis.get('title', '')}
- 核心贡献: {analysis.get('core_contribution', '')}
- 解决的问题: {analysis.get('problem_statement', '')}
- 方法概述: {analysis.get('method_summary', '')}
- 关键结果: {', '.join(analysis.get('key_results', []))}
- 意义: {analysis.get('significance', '')}
- 有趣之处: {', '.join(analysis.get('interesting_aspects', []))}

技术要求:
- 总字数: 约 600 词（3-5 分钟）
- 语速: 正常对话速度
- 风格: 轻松、有趣、易懂

脚本结构:
1. **开场** (约 80-100 词，20-25秒):
   - 抓人眼球的开场白
   - 介绍论文主题
   - 制造一点悬念

2. **问题背景** (约 120-150 词，30-40秒):
   - 这个问题为什么重要？
   - 现有的挑战是什么？

3. **方法介绍** (约 150-200 词，40-50秒):
   - 核心创新点
   - 用类比解释技术概念
   - 避免过多术语

4. **结果与意义** (约 120-150 词，30-40秒):
   - 取得了什么成果？
   - 对领域有什么影响？
   - 实际应用场景

5. **结尾** (约 60-80 词，15-20秒):
   - 总结要点
   - 引发思考或展望未来
   - 自然的结束语

请直接输出脚本内容，用 [开场] [问题] [方法] [结果] [结尾] 标记各段落。
可以在适当位置添加 [pause] 表示停顿，[emphasis] 表示强调。
"""
    
    def _parse_script(self, script_text: str, analysis: Dict) -> Dict:
        """解析脚本文本为结构化格式"""
        
        segments = []
        current_segment = None
        current_text = []
        
        lines = script_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测段落标记
            if '[开场]' in line or '开场' in line[:10]:
                if current_segment:
                    segments.append(self._create_segment(current_segment, current_text))
                current_segment = 'intro'
                current_text = [line.replace('[开场]', '').strip()]
            elif '[问题]' in line or '问题' in line[:10] or '背景' in line[:10]:
                if current_segment:
                    segments.append(self._create_segment(current_segment, current_text))
                current_segment = 'problem'
                current_text = [line.replace('[问题]', '').strip()]
            elif '[方法]' in line or '方法' in line[:10] or '技术' in line[:10]:
                if current_segment:
                    segments.append(self._create_segment(current_segment, current_text))
                current_segment = 'method'
                current_text = [line.replace('[方法]', '').strip()]
            elif '[结果]' in line or '结果' in line[:10] or '意义' in line[:10]:
                if current_segment:
                    segments.append(self._create_segment(current_segment, current_text))
                current_segment = 'results'
                current_text = [line.replace('[结果]', '').strip()]
            elif '[结尾]' in line or '结尾' in line[:10] or '总结' in line[:10]:
                if current_segment:
                    segments.append(self._create_segment(current_segment, current_text))
                current_segment = 'outro'
                current_text = [line.replace('[结尾]', '').strip()]
            else:
                if current_segment:
                    current_text.append(line)
                else:
                    # 默认作为开场
                    current_segment = 'intro'
                    current_text = [line]
        
        # 添加最后一个段落
        if current_segment:
            segments.append(self._create_segment(current_segment, current_text))
        
        # 如果没有解析出段落，按字数分割
        if not segments:
            segments = self._auto_segment(script_text)
        
        # 计算时间
        total_words = sum(s['word_count'] for s in segments)
        estimated_duration = total_words / self.words_per_minute * 60
        
        return {
            'title': analysis.get('title', ''),
            'arxiv_id': analysis.get('arxiv_id', ''),
            'segments': segments,
            'total_word_count': total_words,
            'estimated_duration_seconds': round(estimated_duration, 1),
            'estimated_duration_text': f"{estimated_duration/60:.1f} 分钟",
            'full_text': script_text
        }
    
    def _create_segment(self, seg_type: str, text_lines: List[str]) -> Dict:
        """创建段落对象"""
        text = ' '.join(text_lines)
        word_count = len(text.split())
        duration = word_count / self.words_per_minute * 60
        
        type_names = {
            'intro': '开场',
            'problem': '问题背景',
            'method': '方法介绍',
            'results': '结果与意义',
            'outro': '结尾'
        }
        
        return {
            'type': seg_type,
            'type_name': type_names.get(seg_type, seg_type),
            'text': text,
            'word_count': word_count,
            'estimated_duration_seconds': round(duration, 1)
        }
    
    def _auto_segment(self, text: str) -> List[Dict]:
        """自动分段（备用方案）"""
        words = text.split()
        total_words = len(words)
        
        # 大致分为 5 段
        segment_size = total_words // 5
        
        segments = []
        types = ['intro', 'problem', 'method', 'results', 'outro']
        
        for i, seg_type in enumerate(types):
            start = i * segment_size
            end = start + segment_size if i < 4 else len(words)
            segment_words = words[start:end]
            segment_text = ' '.join(segment_words)
            
            segments.append(self._create_segment(seg_type, [segment_text]))
        
        return segments
    
    def _parse_dialogue_script(self, script_text: str, analysis: Dict) -> Dict:
        """解析双人对话脚本"""
        
        lines = script_text.split('\n')
        dialogue = []
        current_speaker = None
        current_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测说话人
            if line.startswith('小北：') or line.startswith('小北:'):
                if current_speaker and current_text:
                    dialogue.append({
                        'speaker': current_speaker,
                        'text': ' '.join(current_text),
                        'speaker_name': '小北'
                    })
                current_speaker = 'xiaobei'
                current_text = [line.replace('小北：', '').replace('小北:', '').strip()]
            elif line.startswith('阿杰：') or line.startswith('阿杰:'):
                if current_speaker and current_text:
                    dialogue.append({
                        'speaker': current_speaker,
                        'text': ' '.join(current_text),
                        'speaker_name': '阿杰'
                    })
                current_speaker = 'ajie'
                current_text = [line.replace('阿杰：', '').replace('阿杰:', '').strip()]
            else:
                if current_speaker:
                    current_text.append(line)
        
        # 添加最后一段
        if current_speaker and current_text:
            dialogue.append({
                'speaker': current_speaker,
                'text': ' '.join(current_text),
                'speaker_name': '小北' if current_speaker == 'xiaobei' else '阿杰'
            })
        
        # 计算总字数和时长
        total_words = sum(len(d['text'].split()) for d in dialogue)
        estimated_duration = total_words / self.words_per_minute * 60
        
        return {
            'title': analysis.get('title', ''),
            'arxiv_id': analysis.get('arxiv_id', ''),
            'dialogue': dialogue,
            'total_word_count': total_words,
            'estimated_duration_seconds': round(estimated_duration, 1),
            'estimated_duration_text': f"{estimated_duration/60:.1f} 分钟",
            'full_text': script_text
        }
    
    def get_dialogue_text_for_tts(self, script: Dict, speaker: str = None) -> str:
        """获取对话中指定说话人的文本（用于 TTS）"""
        import re
        
        texts = []
        for line in script.get('dialogue', []):
            if speaker is None or line['speaker'] == speaker:
                text = line['text']
                # 移除括号内的动作提示
                text = re.sub(r'[（(].*?[）)]', '', text)
                texts.append(text)
        
        return ' '.join(texts)
    
    def get_full_text_for_tts(self, script: Dict) -> str:
        """获取用于 TTS 的完整文本（去除标记）"""
        # 如果是双人对话格式
        if 'dialogue' in script:
            return self.get_dialogue_text_for_tts(script)
        
        # 单人播客格式
        texts = []
        for seg in script.get('segments', []):
            text = seg['text']
            # 移除标记
            text = text.replace('[pause]', '...')
            text = text.replace('[emphasis]', '')
            # 移除其他方括号内容
            import re
            text = re.sub(r'\[.*?\]', '', text)
            texts.append(text)
        
        return ' '.join(texts)
