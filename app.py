import streamlit as st
from article_fetcher import fetch_article
from utils import generate_prompts, combine_images
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
            if isinstance(article, bytes):
                article = article.decode('utf-8')
            st.success("✅ 文章获取成功")
            
            # 2. 生成提示词
            with st.spinner('正在生成提示词...'):
                prompts = generate_prompts(article)
                if prompts:
                    st.success("✅ 提示词生成成功")
                    with st.expander("查看生成的提示词"):
                        for i, p in enumerate(prompts, 1):
                            st.text(f"提示词 {i}:\n{p}")
            
            # 3. 生成图片
            images = []
            for i, prompt in enumerate(prompts, 1):
                with st.spinner(f'正在生成第 {i} 张图片...'):
                    try:
                        output = replicate.run(
                            "black-forest-labs/flux-schnell",
                            input={
                                "prompt": prompt.encode('utf-8').decode('utf-8'),
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
                        
                        # 使用你的combine_images函数
                        final_img = combine_images(img, LOGO_PATH)
                        
                        images.append(final_img)
                        st.success(f"✅ 第 {i} 张图片生成成功")
                    except Exception as e:
                        st.error(f"生成第 {i} 张图片时出错: {str(e)}")
                
            # 4. 显示结果
            if images:
                st.success("✅ 所有封面生成成功")
                
                # 显示图片
                cols = st.columns(len(images))
                for idx, (col, img) in enumerate(zip(cols, images)):
                    col.image(img, caption=f"封面 {idx+1}", use_container_width=True)
                    
        except Exception as e:
            st.error(f"发生错误: {str(e)}")
            st.error("错误类型: " + str(type(e))) 