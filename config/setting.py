"""配置文件"""
import os

# API配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'your_api_key')
DEEPSEEK_API_URL = os.environ.get('DEEPSEEK_API_URL', 'https://api.deepseek.com')

# 目录配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
INPUT_DIR = os.path.join(DATA_DIR, 'input')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')
CACHE_DIR = os.path.join(DATA_DIR, 'cache')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# 分析维度
ANALYSIS_DIMENSIONS = [
    "基本面及通胀",
    "资金面",
    "货币及财政政策",
    "机构行为",
    "海外及其他"
]

def setup_environment():
    """设置环境"""
    # 创建必要的目录
    for directory in [DATA_DIR, INPUT_DIR, OUTPUT_DIR, CACHE_DIR, LOG_DIR]:
        os.makedirs(directory, exist_ok=True)
