import streamlit as st
from article_fetcher import fetch_article
from utils import generate_prompts, combine_images
from rate_limiter import RateLimiter
import replicate
from PIL import Image
import requests
from io import BytesIO
import os
import hashlib
from config import *
import time

# 初始化速率限制器
rate_limiter = RateLimiter(limit=3, window=24)

st.set_page_config(page_title="活水智能封面生成器", page_icon="🎨")

st.title("活水智能封面生成器 🎨")

def get_user_id():
    """
    获取用户唯一标识
    基于用户的一些持久特征生成一个唯一标识
    """
    try:
        # 使用新的 API 获取用户信息
        user_agent = st.query_params.get('User-Agent', '')
        language = st.query_params.get('Accept-Language', '')
        
        # 组合信息并生成哈希
        user_data = f"{user_agent}_{language}"
        return hashlib.md5(user_data.encode()).hexdigest()
    except:
        # 如果获取失败，生成一个基于会话的ID
        if 'user_id' not in st.session_state:
            st.session_state.user_id = hashlib.md5(str(time.time()).encode()).hexdigest()
        return st.session_state.user_id

# 获取使用情况信息（不增加计数）
user_id = get_user_id()
_, info = rate_limiter.get_usage_info(user_id)

# 显示剩余次数
st.info(f"今日剩余使用次数: {info['remaining_requests']} 次 ({info['reset_in']})")

# 输入区域
url = st.text_input("请输入文章链接：")

if st.button("生成封面"):
    # 只在点击按钮时检查并增加计数
    allowed, info = rate_limiter.check_rate_limit(user_id)
    
    if not allowed:
        st.error(f"已达到今日使用限制，请{info['reset_in']}再试")
    else:
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