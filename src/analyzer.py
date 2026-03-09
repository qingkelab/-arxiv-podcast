"""
内容分析模块 - 使用 LLM 分析论文核心内容
"""
import os
import json
from typing import Dict, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ContentAnalyzer:
    """使用 LLM 分析论文内容，提取核心要点"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.client = OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY'),
            base_url=base_url or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        )
        self.model = "kimi-k2-0711-preview"  # 可以根据需要调整
    
    def analyze(self, paper_data: Dict) -> Dict:
        """分析论文，返回结构化结果"""
        
        # 构建分析提示
        prompt = self._build_analysis_prompt(paper_data)
        
        print("正在分析论文内容...")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位专业的学术论文分析专家。你的任务是深入理解论文内容，提取核心要点，为制作科普播客做准备。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # 解析 JSON 响应
        content = response.choices[0].message.content
        # 提取 JSON 部分
        try:
            # 尝试直接解析
            analysis = json.loads(content)
        except json.JSONDecodeError:
            # 尝试从 markdown 代码块中提取
            import re
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(1))
            else:
                # 手动解析
                analysis = self._parse_text_response(content)
        
        analysis['arxiv_id'] = paper_data.get('arxiv_id', '')
        analysis['title'] = paper_data.get('title', '')
        analysis['authors'] = paper_data.get('authors', [])
        
        return analysis
    
    def _build_analysis_prompt(self, paper_data: Dict) -> str:
        """构建分析提示"""
        
        sections_text = "\n\n".join([
            f"## {s['heading']}\n{s['content'][:500]}"
            for s in paper_data.get('sections', [])[:5]
        ])
        
        images_text = "\n".join([
            f"- 图片{i+1}: {img.get('caption', '无标题')[:100]}"
            for i, img in enumerate(paper_data.get('images', [])[:5])
        ])
        
        prompt = f"""请分析以下学术论文，提取制作科普播客所需的核心信息。

论文标题: {paper_data.get('title', '')}
作者: {', '.join(paper_data.get('authors', [])[:3])}

摘要:
{paper_data.get('abstract', '')[:1000]}

主要章节:
{sections_text}

论文图片:
{images_text}

请以下面的 JSON 格式返回分析结果:

{{
    "core_contribution": "论文的核心贡献是什么？用1-2句话概括",
    "problem_statement": "论文解决的是什么问题？为什么重要？",
    "method_summary": "主要方法/技术是什么？如何工作？",
    "key_results": ["关键结果1", "关键结果2", "关键结果3"],
    "significance": "这项工作的影响和意义是什么？",
    "target_audience": "这个研究对谁最有价值？",
    "interesting_aspects": ["有趣的点1", "有趣的点2"],
    "recommended_images": [0, 1, 2],
    "difficulty_level": "medium",
    "technical_terms": ["术语1: 简单解释", "术语2: 简单解释"]
}}

注意:
1. 用通俗易懂的语言，避免过多术语
2. 思考什么内容会让普通听众感兴趣
3. recommended_images 是推荐使用的图片索引（从0开始）
4. 返回必须是有效的 JSON 格式"""
        
        return prompt
    
    def _parse_text_response(self, content: str) -> Dict:
        """从文本响应中手动提取信息"""
        return {
            "core_contribution": "未能自动解析，请检查 API 响应",
            "problem_statement": "",
            "method_summary": "",
            "key_results": [],
            "significance": "",
            "target_audience": "",
            "interesting_aspects": [],
            "recommended_images": [],
            "difficulty_level": "medium",
            "technical_terms": [],
            "raw_response": content[:500]
        }
    
    def select_images_for_script(self, analysis: Dict, images: List[Dict]) -> List[Dict]:
        """根据分析结果选择最适合播客的图片"""
        recommended_indices = analysis.get('recommended_images', [])
        
        selected = []
        for idx in recommended_indices:
            if 0 <= idx < len(images):
                img = images[idx]
                if img.get('local_path'):
                    selected.append({
                        'path': img['local_path'],
                        'caption': img.get('caption', ''),
                        'context': img.get('context', ''),
                        'use_for': self._determine_image_use(img, analysis)
                    })
        
        # 如果没有推荐图片，选择前3张有本地路径的
        if not selected:
            for img in images[:3]:
                if img.get('local_path'):
                    selected.append({
                        'path': img['local_path'],
                        'caption': img.get('caption', ''),
                        'context': img.get('context', ''),
                        'use_for': 'general'
                    })
        
        return selected
    
    def _determine_image_use(self, image: Dict, analysis: Dict) -> str:
        """确定图片的用途"""
        caption = image.get('caption', '').lower()
        
        if any(kw in caption for kw in ['architecture', 'framework', 'overview', 'system']):
            return 'method'
        elif any(kw in caption for kw in ['result', 'experiment', 'accuracy', 'performance']):
            return 'results'
        elif any(kw in caption for kw in ['figure 1', 'intro']):
            return 'intro'
        else:
            return 'general'
