from article_fetcher import fetch_article

def test_fetch_article():
    # 测试URL
    test_url = input("请输入要测试的文章链接：")
    
    try:
        print("开始获取文章内容...")
        article_text = fetch_article(test_url)
        
        print("\n获取的文章内容：")
        print("=" * 50)
        print(article_text[:500] + "......")  # 只显示前500个字符
        print("=" * 50)
        print(f"\n文章总长度：{len(article_text)} 字符")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    test_fetch_article() 