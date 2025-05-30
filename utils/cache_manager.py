"""缓存管理器 - 统一管理所有缓存功能"""
import os
import json
import hashlib
from datetime import datetime
from typing import Optional
from .file_handler import FileHandler
from .logger import setup_logger


class CacheManager:
    """缓存管理器"""

    def __init__(self):
        self.logger = setup_logger("CacheManager")
        self.file_handler = FileHandler()
        self.hash_cache_file = os.path.join('data', 'cache', 'article_hashes.json')
        self.article_hashes = self._load_article_hashes()

    def _load_article_hashes(self) -> dict:
        """加载已爬取文章的哈希值"""
        if os.path.exists(self.hash_cache_file):
            try:
                with open(self.hash_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_article_hashes(self):
        """保存文章哈希值"""
        os.makedirs(os.path.dirname(self.hash_cache_file), exist_ok=True)
        with open(self.hash_cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.article_hashes, f, ensure_ascii=False, indent=2)

    def _get_article_hash(self, title: str, institution: str, date: str) -> str:
        """生成文章唯一标识哈希"""
        content = f"{title}_{institution}_{date}"
        return hashlib.md5(content.encode()).hexdigest()

    def is_article_processed(self, title: str, institution: str, date: str) -> bool:
        """检查文章是否已处理"""
        article_hash = self._get_article_hash(title, institution, date)
        today = datetime.now().date().isoformat()

        if article_hash in self.article_hashes:
            processed_date = self.article_hashes[article_hash].get('processed_date')
            if processed_date == today:
                return True
        return False

    def mark_article_processed(self, title: str, institution: str, date: str):
        """标记文章已处理"""
        article_hash = self._get_article_hash(title, institution, date)
        self.article_hashes[article_hash] = {
            'title': title,
            'institution': institution,
            'date': date,
            'processed_date': datetime.now().date().isoformat(),
            'processed_time': datetime.now().isoformat()
        }
        self._save_article_hashes()

    def check_cache(self, url: str, date_folder: Optional[str] = None) -> str:
        """检查缓存是否存在"""
        return self.file_handler.check_cache(url, date_folder)

    def save_article_cache(self, url: str, institution: str, date: str,
                           title: str, article_type: str, content: str):
        """保存文章缓存"""
        cache_path = self.file_handler.get_cache_path(
            url, institution, date, title, article_type
        )
        self.file_handler.save_cache(content, cache_path)
        self.logger.info(f"内容已缓存到: {article_type}/{os.path.basename(cache_path)}")

    def get_cache_statistics(self, date_folder: Optional[str] = None) -> dict:
        """获取缓存统计"""
        return self.file_handler.get_cache_statistics(date_folder)

    def clean_old_cache(self, days_to_keep: int = 7):
        """清理旧缓存"""
        self.file_handler.clean_old_cache(days_to_keep)
        self.logger.info(f"已清理{days_to_keep}天前的缓存文件")