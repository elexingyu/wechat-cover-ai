import streamlit as st
from article_fetcher import fetch_article
from utils import generate_prompts
import replicate
from PIL import Image
import requests
from io import BytesIO
import os
from config import *

st.set_page_config(page_title="活水智能封面生成器", page_icon="🎨")

st.title("活水智能封面生成器 🎨")

# 输入区域
url = st.text_input("请输入文章链接：")

if st.button("生成封面"):
    with st.spinner('处理中...'):
        try:
            # 1. 获取文章
            article = fetch_article(url)
            st.success("✅ 文章获取成功")
            
            # 2. 生成提示词
            prompts = generate_prompts(article)
            st.success("✅ 提示词生成成功")
            
            # 3. 生成图片
            images = []
            for i, prompt in enumerate(prompts, 1):
                st.write(f"正在生成第 {i} 张图片...")
                output = replicate.run(
                    "black-forest-labs/flux-schnell",
                    input={
                        "prompt": prompt,
                        "go_fast": True,
                        "num_outputs": 1,
                        "aspect_ratio": "16:9",
                        "output_format": "webp",
                        "output_quality": 90
                    }
                )
                
                # 下载图片
                response = requests.get(output[0])
                img = Image.open(BytesIO(response.content))
                
                # 与logo合成
                template = Image.open(LOGO_PATH)
                final_img = Image.new('RGBA', template.size)
                final_img.paste(img, (0, 0))
                final_img.paste(template, (0, 0), template)
                
                images.append(final_img)
                
            # 4. 显示结果
            st.success("✅ 封面生成成功")
            
            # 显示图片
            cols = st.columns(len(images))
            for idx, (col, img) in enumerate(zip(cols, images)):
                col.image(img, caption=f"封面 {idx+1}", use_column_width=True)
                
        except Exception as e:
            st.error(f"发生错误: {str(e)}") 