"""文件处理工具"""
import os
import hashlib
import pandas as pd
from typing import List, Tuple
from config.setting import INPUT_DIR, CACHE_DIR


class FileHandler:
    """文件处理器"""

    @staticmethod
    def read_excel_links(file_name: str) -> Tuple[List[str], List[str], List[str], List[str]]:
        """从Excel读取链接"""
        file_path = os.path.join(INPUT_DIR, file_name)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        df = pd.read_excel(file_path)

        links = df['链接'].dropna().tolist()
        institutions = df['撰写机构'].tolist() if '撰写机构' in df.columns else [''] * len(links)
        dates = df['发布日期'].tolist() if '发布日期' in df.columns else [''] * len(links)
        contents = df['文章内容'].tolist() if '文章内容' in df.columns else [None] * len(links)

        return links, institutions, dates, contents

    @staticmethod
    def get_cache_path(url: str, institution: str, date: str, title: str = "") -> str:
        """获取缓存文件路径"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        date_str = str(date).replace('/', '-').replace(' ', '_')[:10] if date else "未知日期"

        # 清理文件名
        title_clean = FileHandler._sanitize_filename(title) if title else "未知标题"

        filename = f"{institution}_{date_str}_{title_clean}_{url_hash}.txt"
        return os.path.join(CACHE_DIR, filename)

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """清理文件名"""
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        if len(filename) > 100:
            filename = filename[:100]
        return filename.strip()

    @staticmethod
    def check_cache(url: str) -> str:
        """检查缓存是否存在"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]

        if os.path.exists(CACHE_DIR):
            for file in os.listdir(CACHE_DIR):
                if url_hash in file:
                    cache_file = os.path.join(CACHE_DIR, file)
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return f.read()

        return ""

    @staticmethod
    def save_cache(content: str, cache_path: str):
        """保存缓存"""
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(content)