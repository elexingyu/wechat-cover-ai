import os
import replicate
import requests
from PIL import Image
import io
from config import *

def test_generate_image():
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    test_prompt = "black forest gateau cake spelling out the words \"FLUX SCHNELL\", tasty, food photography, dynamic shot"
    
    try:
        print("开始生成图片...")
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": test_prompt,
                "go_fast": True,
                "num_outputs": 1,
                "aspect_ratio": "16:9",  # 设置为我们需要的宽高比
                "output_format": "png",
                "output_quality": 90
            }
        )
        
        print("下载生成的图片...")
        response = requests.get(output[0])
        img = Image.open(io.BytesIO(response.content))
        
        output_path = os.path.join(OUTPUT_DIR, "test_output.png")
        img.save(output_path)
        print(f"实际图片尺寸: {img.size}")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    test_generate_image() 