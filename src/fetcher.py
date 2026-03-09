"""
Arxiv 论文获取模块
"""
import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict, Optional


class ArxivFetcher:
    """获取 arxiv 论文 HTML 版本并提取内容"""
    
    def __init__(self):
        self.base_url = "https://arxiv.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        })
    
    def extract_arxiv_id(self, url: str) -> str:
        """从各种 arxiv URL 格式中提取 ID"""
        patterns = [
            r'arxiv\.org/abs/(\d+\.\d+)',
            r'arxiv\.org/html/(\d+\.\d+)',
            r'arxiv\.org/pdf/(\d+\.\d+)',
            r'(\d{4}\.\d{4,5})',  # 纯 ID 格式
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError(f"无法从 URL 中提取 arxiv ID: {url}")
    
    def fetch_html(self, arxiv_id: str) -> str:
        """获取论文 HTML 内容"""
        html_url = f"{self.base_url}/html/{arxiv_id}"
        print(f"正在获取: {html_url}")
        
        response = self.session.get(html_url, timeout=30)
        response.raise_for_status()
        return response.text
    
    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """提取论文中的所有图片"""
        images = []
        
        # 查找所有 figure 标签
        for idx, figure in enumerate(soup.find_all('figure')):
            img_tag = figure.find('img')
            if not img_tag:
                continue
            
            # 获取图片 URL
            img_src = img_tag.get('src', '')
            if img_src.startswith('/'):
                img_url = urljoin(base_url, img_src)
            elif img_src.startswith('http'):
                img_url = img_src
            else:
                img_url = urljoin(f"{self.base_url}/html/", img_src)
            
            # 获取 caption
            caption_tag = figure.find('figcaption')
            caption = caption_tag.get_text(strip=True) if caption_tag else ""
            
            # 获取图片上下文（前后段落）
            context = ""
            prev_p = figure.find_previous('p')
            if prev_p:
                context = prev_p.get_text(strip=True)[:200]
            
            images.append({
                'id': idx,
                'url': img_url,
                'caption': caption,
                'context': context,
                'local_path': None
            })
        
        return images
    
    def download_images(self, images: List[Dict], output_dir: Path) -> List[Dict]:
        """下载图片到本地"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for img in images:
            try:
                response = self.session.get(img['url'], timeout=30)
                response.raise_for_status()
                
                # 确定文件扩展名
                content_type = response.headers.get('content-type', '')
                if 'png' in content_type:
                    ext = 'png'
                elif 'jpeg' in content_type or 'jpg' in content_type:
                    ext = 'jpg'
                else:
                    ext = 'png'
                
                local_path = output_dir / f"figure_{img['id']}.{ext}"
                local_path.write_bytes(response.content)
                img['local_path'] = str(local_path)
                print(f"  下载图片: {local_path.name}")
                
            except Exception as e:
                print(f"  下载失败 {img['url']}: {e}")
                img['local_path'] = None
        
        return images
    
    def parse_paper(self, html_content: str) -> Dict:
        """解析论文 HTML 内容"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 提取标题
        title_tag = soup.find('h1', class_='title') or soup.find('h1')
        title = title_tag.get_text(strip=True).replace('Title:', '').strip() if title_tag else "Unknown"
        
        # 提取摘要
        abstract_div = soup.find('div', class_='abstract') or soup.find('section', {'id': 'abstract'})
        abstract = ""
        if abstract_div:
            abstract = abstract_div.get_text(strip=True).replace('Abstract', '').strip()
        
        # 提取作者
        authors = []
        author_tags = soup.find_all('div', class_='author') or soup.find_all('a', {'href': re.compile(r'/search.*author')})
        for tag in author_tags[:5]:  # 限制作者数量
            author_name = tag.get_text(strip=True)
            if author_name and len(author_name) < 100:
                authors.append(author_name)
        
        # 提取章节内容
        sections = []
        for section in soup.find_all('section'):
            heading = section.find(['h2', 'h3'])
            if heading:
                heading_text = heading.get_text(strip=True)
                # 获取段落文本
                paragraphs = section.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])
                
                if len(content) > 100:  # 过滤空章节
                    sections.append({
                        'heading': heading_text,
                        'content': content[:2000],  # 限制长度
                        'level': 2 if heading.name == 'h2' else 3
                    })
        
        # 提取图片
        images = self.extract_images(soup, self.base_url)
        
        return {
            'title': title,
            'abstract': abstract,
            'authors': list(set(authors))[:5],  # 去重并限制
            'sections': sections[:10],  # 限制章节数量
            'images': images,
            'raw_html': html_content
        }
    
    def fetch(self, url: str, output_dir: Path) -> Dict:
        """完整的获取流程"""
        arxiv_id = self.extract_arxiv_id(url)
        print(f"提取到 arxiv ID: {arxiv_id}")
        
        # 获取 HTML
        html_content = self.fetch_html(arxiv_id)
        
        # 解析内容
        paper_data = self.parse_paper(html_content)
        paper_data['arxiv_id'] = arxiv_id
        
        # 下载图片
        if paper_data['images']:
            images_dir = output_dir / 'images'
            paper_data['images'] = self.download_images(paper_data['images'], images_dir)
        
        return paper_data
