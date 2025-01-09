from utils import generate_prompts

def test_generate_prompts():
    # 测试文章
    test_article = """
    如果你想从零开始学习机器学习，这篇指南值得你看看！💡

作者用6年的时间从零到成为顶级AI初创公司的研究科学家，现在回头总结了最有效的学习路径。如果你也想踏入ML领域，这里是他建议的关键步骤👇：

## 1. Python 是起点，但别学太多！
- 学会基础：列表、字典、if-else、for循环等。
- 进阶一点：列表推导式、类继承。
- 学完就动手：做点有趣的小项目，比如计算器、贪吃蛇游戏或简单网站。  

## 2. 数学：真的没你想的那么难！
- 你只需要掌握：
  - 基本微积分（导数为主，积分很少用）。
  - 矩阵和向量的基本运算。
  - 概率论核心概念（比如贝叶斯公式）。
  
## 3. 机器学习：从基础到实践
- 经典ML是基础：别直接跳到深度学习！  
- 推荐 Andrew Ng 的课程，涵盖逻辑回归、决策树等。
    """
    
    try:
        # 生成提示词
        print("开始生成提示词...")
        prompts = generate_prompts(test_article)
        
        # 打印结果
        print("\n生成的提示词：")
        for i, prompt in enumerate(prompts, 1):
            print(f"\n{i}. {prompt}")
            print(f"长度: {len(prompt)} 字符")
            
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    test_generate_prompts() 