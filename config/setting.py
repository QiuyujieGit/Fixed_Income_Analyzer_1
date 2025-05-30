"""配置文件"""
import os

# API配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'your-api-key')

# 目录配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
INPUT_DIR = os.path.join(DATA_DIR, 'input')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')
CACHE_DIR = os.path.join(DATA_DIR, 'cache')

# 分析维度
ANALYSIS_DIMENSIONS = [
    "基本面及通胀",
    "资金面",
    "货币及财政政策",
    "机构行为",
    "海外及其他"
]

# 评分权重
SCORE_WEIGHTS = {
    '数据支撑': 0.25,
    '逻辑完整': 0.20,
    '策略价值': 0.25,
    '观点独特': 0.15,
    '市场影响': 0.15
}

def setup_environment():
    """设置环境"""
    # 创建必要的目录
    for directory in [DATA_DIR, INPUT_DIR, OUTPUT_DIR, CACHE_DIR]:
        os.makedirs(directory, exist_ok=True)
