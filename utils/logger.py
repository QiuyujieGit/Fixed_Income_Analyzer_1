"""日志管理工具 - 统一版本"""
import os
import logging
from datetime import datetime
from config.setting import LOG_DIR

# 全局日志器实例
_logger_instance = None

def setup_logger(name: str = "BondAnalyzer") -> logging.Logger:
    """设置日志器 - 使用单一日志文件"""
    global _logger_instance

    # 如果已经创建了主日志器，返回子日志器
    if _logger_instance:
        return logging.getLogger(name)

    # 确保日志目录存在
    os.makedirs(LOG_DIR, exist_ok=True)

    # 创建主日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 清除已有的处理器
    root_logger.handlers.clear()

    # 创建单一的日志文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(LOG_DIR, f'BondAnalyzer_{timestamp}.log')

    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器到根日志器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # 标记已创建
    _logger_instance = root_logger

    # 返回具名日志器
    return logging.getLogger(name)
