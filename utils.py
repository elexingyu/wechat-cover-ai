import requests
from PIL import Image
from config import *
from openai import OpenAI

def generate_prompts(article_text):
    """使用Deepseek生成图像提示词"""
    # 定义默认提示词
    default_prompts = [
        "A modern tech command center with holographic displays showing Python code, cyberpunk style, blue and red neon lighting, highly detailed 8k rendering",
        "Futuristic learning environment with flowing data streams, abstract neural networks, cool blue tones with bright accent lights, professional style",
        "High-tech classroom with dynamic lighting, modern minimalist design, subtle gradients from deep blue to purple, clean professional atmosphere"
    ]
    
    try:
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        
        # 确保文本是 UTF-8 编码
        if isinstance(article_text, bytes):
            article_text = article_text.decode('utf-8')
        
        system_prompt = """你是一个专业的AI艺术提示词专家。
        请根据给定的文章内容，生成3个不同的英文提示词，用于AI绘图。
        要求：
        1. 提示词要体现文章的核心内容和主题
        2. 风格要现代、科技感、未来感
        3. 要加入具体的艺术风格描述，如lighting, color scheme等
        4. 每个提示词长度在100-150字之间
        5. 直接返回3个提示词，每个提示词用 ### 分隔，不要加序号或其他标记"""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请根据以下文章生成提示词：\n\n{article_text}"}
            ],
            temperature=0.7
        )
        
        # 处理返回的提示词
        content = response.choices[0].message.content.strip()
        prompts = [p.strip() for p in content.split('###') if p.strip()]
        
        # 确保有3个提示词
        while len(prompts) < 3:
            prompts.append(default_prompts[len(prompts)])
            
        return prompts[:3]  # 确保只返回3个提示词
        
    except Exception as e:
        print(f"生成提示词时出错: {str(e)}")
        return default_prompts  # 发生错误时返回默认提示词

def combine_images(cover_img, logo_img, x_pos=90, y_pos=90, size_percent=15, opacity=100):
    """
    将logo添加到封面图片上
    
    参数:
    - cover_img: 封面图片
    - logo_img: logo图片
    - x_pos: logo水平位置（0-100）
    - y_pos: logo垂直位置（0-100）
    - size_percent: logo大小（占图片宽度的百分比）
    - opacity: logo不透明度（0-100）
    """
    # 转换为RGBA模式以支持透明度
    cover_img = cover_img.convert('RGBA')
    logo_img = logo_img.convert('RGBA')
    
    # 计算logo的目标大小
    target_width = int(cover_img.width * (size_percent / 100))
    aspect_ratio = logo_img.width / logo_img.height
    target_height = int(target_width / aspect_ratio)
    
    # 调整logo大小
    logo_img = logo_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    # 计算实际位置
    x = int((cover_img.width - target_width) * x_pos / 100)
    y = int((cover_img.height - target_height) * y_pos / 100)
    
    # 处理透明度
    if opacity < 100:
        logo_img.putalpha(Image.new('L', logo_img.size, int(255 * opacity / 100)))
    
    # 创建新图片
    final_img = Image.new('RGBA', cover_img.size)
    final_img.paste(cover_img, (0, 0))
    final_img.paste(logo_img, (x, y), logo_img)
    
    return final_img.convert('RGB')  # 转回RGB模式 