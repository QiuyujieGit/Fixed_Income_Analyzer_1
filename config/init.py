"""配置模块"""
from setting import (
    # API配置
    DEEPSEEK_API_KEY,
    DEEPSEEK_API_URL,

    # 目录配置
    BASE_DIR,
    DATA_DIR,
    INPUT_DIR,
    OUTPUT_DIR,
    CACHE_DIR,
    LOG_DIR,

    # 分析配置
    ANALYSIS_DIMENSIONS
)

__all__ = [
    'DEEPSEEK_API_KEY',
    'DEEPSEEK_API_URL',
    'BASE_DIR',
    'DATA_DIR',
    'INPUT_DIR',
    'OUTPUT_DIR',
    'CACHE_DIR',
    'LOG_DIR',
    'ANALYSIS_DIMENSIONS'
]