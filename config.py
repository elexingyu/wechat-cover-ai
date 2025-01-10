import os
from dotenv import load_dotenv
import yaml

# 加载.env文件
load_dotenv()

# 获取项目根目录路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# API Keys
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# 路径配置
LOGO_PATH = os.path.join(ROOT_DIR, 'static', 'images', 'huoshuiai_logo.png')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'output')

# 认证配置
AUTH_CONFIG_PATH = os.path.join(ROOT_DIR, 'auth_config.yaml')

def load_auth_config():
    if os.path.exists(AUTH_CONFIG_PATH):
        with open(AUTH_CONFIG_PATH) as file:
            return yaml.safe_load(file)
    return None

# 验证必要的环境变量和文件
def validate_env():
    required_vars = ['REPLICATE_API_TOKEN', 'DEEPSEEK_API_KEY', 'AUTH_SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    if not os.path.exists(LOGO_PATH):
        raise FileNotFoundError(f"Logo file not found at: {LOGO_PATH}")
    
    if not os.path.exists(AUTH_CONFIG_PATH):
        raise FileNotFoundError(f"Auth config file not found at: {AUTH_CONFIG_PATH}")

validate_env() 