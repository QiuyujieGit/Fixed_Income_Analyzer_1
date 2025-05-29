"""Jina Reader爬虫"""
import requests
from .base_crawler import BaseCrawler


class JinaCrawler(BaseCrawler):
    """使用Jina Reader API获取网页内容"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://r.jina.ai/"
        self.timeout = 30

    def fetch_content(self, url: str) -> tuple[str, str]:
        """获取网页内容

        Args:
            url: 目标网页URL

        Returns:
            tuple: (content, title) 内容和标题
        """
        try:
            # 构建Jina Reader URL
            jina_url = f"{self.base_url}{url}"
            self.logger.info(f"使用Jina Reader获取: {jina_url}")

            # 发送请求
            response = requests.get(jina_url, timeout=self.timeout)
            response.raise_for_status()

            # Jina Reader返回的是纯文本内容
            content = response.text

            # 尝试从内容中提取标题（通常在第一行）
            lines = content.split('\n')
            title = lines[0] if lines else ""

            self.logger.info(f"成功获取内容，长度: {len(content)} 字符")
            return content, title

        except requests.Timeout:
            self.logger.error(f"请求超时: {url}")
            return "", ""
        except requests.RequestException as e:
            self.logger.error(f"请求失败: {e}")
            return "", ""
        except Exception as e:
            self.logger.error(f"获取内容失败: {e}")
            return "", ""

    def is_valid_url(self, url: str) -> bool:
        """检查是否是有效的URL（非微信文章）"""
        # Jina Reader可以处理大部分网页，除了需要特殊处理的
        excluded_domains = [
            "mp.weixin.qq.com",  # 微信文章
            "localhost",
            "127.0.0.1"
        ]

        for domain in excluded_domains:
            if domain in url:
                return False

        return url.startswith(("http://", "https://"))