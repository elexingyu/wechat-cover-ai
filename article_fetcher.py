import requests
from bs4 import BeautifulSoup
import re
from openai import OpenAI
from config import DEEPSEEK_API_KEY

def analyze_html_structure(html_content):
    """使用 AI 分析网页结构并返回最可能包含文章内容的选择器"""
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
    
    system_prompt = """你是一个网页解析专家。分析给定的HTML结构，找出最可能包含主要文章内容的CSS选择器。
    返回格式要求：
    1. 只返回一个最可能的CSS选择器字符串
    2. 不要包含任何解释或其他文字
    3. 选择器应该尽可能精确，避免获取导航栏、页脚等无关内容
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"分析此HTML并返回最佳选择器：\n\n{html_content[:5000]}"}  # 只发送前5000字符避免token限制
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    except:
        return None

def fetch_article(url):
    """从网页链接获取文章内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 首先尝试常见的选择器
        common_selectors = [
            'article', '.post-content', '.article-content',
            '.entry-content', '.article-body', '.post-body'
        ]
        
        for selector in common_selectors:
            content = soup.select_one(selector)
            if content and len(content.get_text().strip()) > 200:  # 确保内容足够长
                return clean_text(content.get_text())
        
        # 2. 如果常见选择器失败，使用AI分析
        print("自动获取失败，开始使用AI分析网页结构")
        ai_selector = analyze_html_structure(response.text)
        if ai_selector:
            content = soup.select_one(ai_selector)
            if content and len(content.get_text().strip()) > 200:
                return clean_text(content.get_text())
        
        # 3. 后备方案：获取所有段落
        paragraphs = soup.find_all('p')
        text = '\n\n'.join(p.get_text() for p in paragraphs if len(p.get_text().strip()) > 20)
        
        return clean_text(text)
        
    except Exception as e:
        raise Exception(f"获取文章失败: {str(e)}")

def clean_text(text):
    """清理和格式化文本"""
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    # 规范化段落
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # 移除特殊字符
    text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?，。！？、:：()（）\n]', '', text)
    return text.strip() 