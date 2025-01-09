import os
import replicate
import requests
from PIL import Image
import io
from config import *
from utils import generate_prompts, combine_images
from article_fetcher import fetch_article

class CoverGenerator:
    def __init__(self):
        pass
        
    def generate_cover_images(self, article_text):
        # 1. 生成提示词
        prompts = generate_prompts(article_text)
        
        # 2. 为每个提示词生成图片
        generated_images = []
        for prompt in prompts:
            output = replicate.run(
                "black-forest-labs/flux-schnell",
                input={
                    "prompt": prompt,
                    "go_fast": True,
                    "num_outputs": 4,
                    "aspect_ratio": "16:9",  # 目前模型只支持16:9
                    "output_format": "webp",
                    "output_quality": 100
                }
            )
            
            # 下载生成的图片
            response = requests.get(output[0])
            img = Image.open(io.BytesIO(response.content))
            generated_images.append(img)
            
        # 3. 与logo合成
        final_covers = []
        for idx, img in enumerate(generated_images):
            output_path = os.path.join(OUTPUT_DIR, f"cover_{idx+1}.png")
            combined_img = combine_images(img, LOGO_PATH)
            combined_img.save(output_path)
            final_covers.append(output_path)
            
        return final_covers

    def generate_from_url(self, url):
        """从URL生成封面图片"""
        try:
            # 1. 获取文章内容
            print("正在获取文章内容...")
            article_text = fetch_article(url)
            
            # 2. 生成封面
            return self.generate_cover_images(article_text)
            
        except Exception as e:
            print(f"生成封面失败: {str(e)}")
            return []

def main():
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 测试URL
    url = input("请输入文章链接：")
    
    generator = CoverGenerator()
    cover_paths = generator.generate_from_url(url)
    
    if cover_paths:
        print(f"生成的封面图片保存在: {cover_paths}")
    else:
        print("封面生成失败")

if __name__ == "__main__":
    main() 