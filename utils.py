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

def combine_images(cover_img, logo_path):
    """
    使用logo图片作为模板，将生成的图片调整为背景
    """
    # 打开logo图片作为模板
    template = Image.open(logo_path)
    template_width, template_height = template.size
    
    # 调整生成图片的大小以适应模板
    # 计算缩放比例，确保图片能完全覆盖模板
    cover_ratio = cover_img.width / cover_img.height
    template_ratio = template_width / template_height
    
    if cover_ratio > template_ratio:
        # 如果生成的图片更宽，按高度缩放
        new_height = template_height
        new_width = int(new_height * cover_ratio)
    else:
        # 如果生成的图片更高，按宽度缩放
        new_width = template_width
        new_height = int(new_width / cover_ratio)
    
    # 调整生成图片的大小
    cover_img = cover_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 居中裁剪
    left = (new_width - template_width) // 2
    top = (new_height - template_height) // 2
    cover_img = cover_img.crop((left, top, left + template_width, top + template_height))
    
    # 创建最终图片
    final_img = Image.new('RGBA', (template_width, template_height))
    
    # 放置背景图
    final_img.paste(cover_img, (0, 0))
    
    # 放置logo（使用alpha通道）
    final_img.paste(template, (0, 0), template)
    
    return final_img 