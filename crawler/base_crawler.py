"""爬虫基类"""
from abc import ABC, abstractmethod
import logging


class BaseCrawler(ABC):
    """爬虫基类"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def fetch_content(self, url: str) -> tuple[str, str]:
        """获取内容

        Returns:
            tuple: (content, title)
        """
        pass

    @abstractmethod
    def is_valid_url(self, url: str) -> bool:
        """检查URL是否有效"""
        pass