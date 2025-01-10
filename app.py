import streamlit as st
from article_fetcher import fetch_article, clean_text
from utils import generate_prompts, combine_images
from rate_limiter import RateLimiter
import replicate
from PIL import Image
import requests
from io import BytesIO
import os
from config import *

# 页面配置
st.set_page_config(page_title="活水-微信公众号封面生成器", page_icon="🎨")

# 显示标题
st.title("活水智能封面生成器 🎨")

# 使用固定的测试用户ID
user_id = "test_user"

# 初始化速率限制器
rate_limiter = RateLimiter(limit=3, window=24)

# 获取使用情况信息
_, info = rate_limiter.get_usage_info(user_id)

# 显示剩余次数
st.info(f"今日剩余使用次数: {info['remaining_requests']} 次 ({info['reset_in']})")

# 添加文本输入框和字数统计
article_text = st.text_area(
    "请输入文章内容：",
    height=300,
    help="建议输入300-2000字的文章内容，以获得最佳效果"
)[:3000]  # 只取前3000字

# 显示字数统计
word_count = len(article_text.strip())
st.caption(f"当前字数: {word_count} 字{' (已截断)' if len(article_text) == 3000 else ''}")

# Logo 上传和配置部分
with st.expander("Logo 设置（可选）"):
    # Logo 上传
    uploaded_logo = st.file_uploader(
        "上传品牌Logo（可选）",
        type=['png', 'jpg', 'jpeg'],
        help="建议使用透明背景的PNG图片，以获得最佳效果"
    )
    
    if uploaded_logo:
        # 创建一个预览画布
        preview_width = 800  # 预览宽度
        preview_height = int(preview_width / 2.35)  # 2.35:1 的高度
        
        # 创建示例背景图
        preview_bg = Image.new('RGB', (preview_width, preview_height), (240, 240, 240))
        
        # 加载logo
        logo_img = Image.open(uploaded_logo)
        
        # 如果是RGBA模式，裁剪掉透明边缘
        if logo_img.mode == 'RGBA':
            # 获取alpha通道
            alpha = logo_img.split()[3]
            # 获取非透明区域的边界框
            bbox = alpha.getbbox()
            if bbox:
                # 裁剪到非透明区域
                logo_img = logo_img.crop(bbox)
        
        # 使用 columns 布局调整控件
        col1, col2 = st.columns([2, 1])
        
        with col2:
            # Logo 大小控制
            logo_size = st.slider(
                "Logo 大小 (%)",
                min_value=5,
                max_value=30,
                value=15
            )
            
            # Logo 位置控制
            x_pos = st.slider(
                "水平位置 (%)",
                min_value=0,
                max_value=100,
                value=90
            )
            
            y_pos = st.slider(
                "垂直位置 (%)",
                min_value=0,
                max_value=100,
                value=90
            )
            
            # Logo 透明度
            opacity = st.slider(
                "不透明度 (%)",
                min_value=0,
                max_value=100,
                value=100
            )
        
        with col1:
            # 计算 logo 实际大小和位置
            logo_width = int(preview_width * logo_size / 100)
            aspect_ratio = logo_img.width / logo_img.height
            logo_height = int(logo_width / aspect_ratio)
            
            # 调整 logo 大小
            logo_img = logo_img.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            # 计算位置
            x = int((preview_width - logo_width) * x_pos / 100)
            y = int((preview_height - logo_height) * y_pos / 100)
            
            # 创建预览图
            preview = preview_bg.copy()
            if logo_img.mode == 'RGBA':
                # 处理透明度
                logo_with_opacity = logo_img.copy()
                if opacity < 100:
                    # 获取alpha通道
                    alpha = logo_with_opacity.split()[3]
                    # 调整alpha通道的值
                    alpha = alpha.point(lambda x: int(x * opacity / 100))
                    # 将调整后的alpha通道放回图片
                    logo_with_opacity.putalpha(alpha)
                preview.paste(logo_with_opacity, (x, y), logo_with_opacity)
            else:
                # 如果不是RGBA模式，先转换
                logo_with_opacity = logo_img.convert('RGBA')
                if opacity < 100:
                    # 创建新的alpha通道
                    alpha = Image.new('L', logo_img.size, int(255 * opacity / 100))
                    logo_with_opacity.putalpha(alpha)
                preview.paste(logo_with_opacity, (x, y), logo_with_opacity)
            
            # 显示预览
            st.image(preview, caption="Logo 位置预览", use_column_width=True)
            
            # 添加网格线帮助对齐
            if st.checkbox("显示网格线", value=False, key="show_grid"):
                # 在预览图上绘制网格线
                from PIL import ImageDraw
                draw = ImageDraw.Draw(preview)
                # 绘制水平和垂直线
                for i in range(0, preview_width, 100):
                    draw.line([(i, 0), (i, preview_height)], fill=(200, 200, 200), width=1)
                for i in range(0, preview_height, 100):
                    draw.line([(0, i), (preview_width, i)], fill=(200, 200, 200), width=1)
                st.image(preview, caption="Logo 位置预览（带网格）", use_column_width=True)

if st.button("生成封面"):
    if word_count < 50:
        st.error("文章内容太短,请至少输入50个字")
        st.stop()
    if word_count > 3000:
        st.error("文章内容太长,请控制在3000字以内")
        st.stop()
        
    # 只在点击按钮时检查并增加计数
    allowed, info = rate_limiter.check_rate_limit(user_id)
    
    if not allowed:
        st.error(f"已达到今日使用限制，请{info['reset_in']}再试")
    else:
        with st.spinner('处理中...'):
            try:
                # 清理文本
                article = clean_text(article_text)
                st.success("✅ 文章处理成功")
                
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
                            
                            # 打印实际图片尺寸，帮助调试
                            st.write(f"生成图片尺寸: {img.size}")
                            
                            # 根据用户设置处理logo
                            if uploaded_logo:
                                logo_img = Image.open(uploaded_logo)
                                # 如果是RGBA模式，裁剪掉透明边缘
                                if logo_img.mode == 'RGBA':
                                    alpha = logo_img.split()[3]
                                    bbox = alpha.getbbox()
                                    if bbox:
                                        logo_img = logo_img.crop(bbox)
                                
                                # 直接使用百分比计算实际尺寸
                                target_width = int(img.width * logo_size / 100)
                                aspect_ratio = logo_img.width / logo_img.height
                                target_height = int(target_width / aspect_ratio)
                                
                                # 调整logo大小
                                logo_img = logo_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                                
                                # 计算实际位置
                                x = int((img.width - target_width) * x_pos / 100)
                                y = int((img.height - target_height) * y_pos / 100)
                                
                                # 处理透明度
                                if logo_img.mode == 'RGBA':
                                    logo_with_opacity = logo_img.copy()
                                    if opacity < 100:
                                        alpha = logo_with_opacity.split()[3]
                                        alpha = alpha.point(lambda x: int(x * opacity / 100))
                                        logo_with_opacity.putalpha(alpha)
                                else:
                                    logo_with_opacity = logo_img.convert('RGBA')
                                    if opacity < 100:
                                        alpha = Image.new('L', logo_img.size, int(255 * opacity / 100))
                                        logo_with_opacity.putalpha(alpha)
                                
                                # 合成图片
                                img = img.convert('RGBA')
                                img.paste(logo_with_opacity, (x, y), logo_with_opacity)
                                img = img.convert('RGB')
                            
                            images.append(img)
                            st.success(f"✅ 第 {i} 张图片生成成功")
                        except Exception as e:
                            st.error(f"生成第 {i} 张图片时出错: {str(e)}")
                
                # 4. 显示结果
                if images:
                    st.success("✅ 所有封面生成成功")
                    
                    # 显示图片并添加下载按钮
                    cols = st.columns(len(images))
                    for idx, (col, img) in enumerate(zip(cols, images)):
                        # 显示图片
                        col.image(img, caption=f"封面 {idx+1}", use_container_width=True)
                        
                        # 将图片转换为 base64
                        import base64
                        from io import BytesIO
                        
                        buffered = BytesIO()
                        img.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        
                        # 创建下载链接
                        href = f"""
                        <a href="data:image/png;base64,{img_str}" 
                           download="cover_{idx+1}.png" 
                           style="text-decoration: none; width: 100%; display: block; text-align: center;">
                            <button style="
                                background-color: #4CAF50;
                                border: none;
                                color: white;
                                padding: 8px 16px;
                                text-align: center;
                                text-decoration: none;
                                display: inline-block;
                                font-size: 14px;
                                margin: 4px 2px;
                                cursor: pointer;
                                border-radius: 4px;
                                transition: background-color 0.3s;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                width: 80%;">
                                下载封面 {idx+1}
                            </button>
                        </a>
                        """
                        col.markdown(href, unsafe_allow_html=True)
                    
                    # 添加全部下载按钮
                    st.markdown("<br>", unsafe_allow_html=True)  # 添加间距
                    
                    # 创建ZIP文件
                    import zipfile
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                        for idx, img in enumerate(images, 1):
                            img_byte_arr = BytesIO()
                            img.save(img_byte_arr, format='PNG')
                            img_byte_arr = img_byte_arr.getvalue()
                            zip_file.writestr(f'cover_{idx}.png', img_byte_arr)
                    
                    # 将ZIP文件转换为base64
                    zip_str = base64.b64encode(zip_buffer.getvalue()).decode()
                    
                    # 创建全部下载按钮
                    all_download_href = f"""
                    <div style="text-align: center;">
                        <a href="data:application/zip;base64,{zip_str}" 
                           download="all_covers.zip" 
                           style="text-decoration: none;">
                            <button style="
                                background-color: #2196F3;
                                border: none;
                                color: white;
                                padding: 12px 24px;
                                text-align: center;
                                text-decoration: none;
                                display: inline-block;
                                font-size: 16px;
                                margin: 8px 2px;
                                cursor: pointer;
                                border-radius: 4px;
                                transition: background-color 0.3s;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                width: 200px;">
                                下载全部封面
                            </button>
                        </a>
                    </div>
                    """
                    st.markdown(all_download_href, unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"发生错误: {str(e)}")
                st.error("错误类型: " + str(type(e))) 