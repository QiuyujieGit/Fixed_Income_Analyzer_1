"""爬虫管理器 - 统一管理所有爬虫功能"""
import os
from datetime import datetime, date
from typing import List, Dict
from .wechat_batch_crawler import WechatBatchCrawler
from .wechat_crawler import WechatCrawler
from .jina_crawler import JinaCrawler
from utils.logger import setup_logger
from utils.cache_manager import CacheManager
from utils.data_processor import DataProcessor


class CrawlerManager:
    """爬虫管理器 - 只负责爬取功能"""

    def __init__(self):
        self.logger = setup_logger("CrawlerManager")
        self.batch_crawler = WechatBatchCrawler()
        self.wechat_crawler = WechatCrawler()
        self.jina_crawler = JinaCrawler()
        self.cache_manager = CacheManager()
        self.data_processor = DataProcessor()

    def crawl_articles(self) -> List[Dict]:
        """爬取文章的主入口"""
        # 加载公众号列表
        if not self.batch_crawler.load_accounts():
            self.logger.error("加载公众号列表失败")
            return []

        # 询问爬取选项
        days, only_today = self._get_crawl_options()

        # 开始爬取
        self.logger.info(f"开始爬取最近{days}天的文章...")
        articles = self._crawl_with_dedup(days, only_today)

        # 显示缓存统计
        self.cache_manager.show_today_statistics()

        return articles  # 直接返回文章，不做筛选

    def _get_crawl_options(self) -> tuple:
        """获取爬取选项"""
        print("\n爬取选项:")
        print("1. 只爬取今日文章（推荐）")
        print("2. 爬取最近N天文章")

        crawl_option = input("\n请选择 (1/2): ")

        if crawl_option == '1':
            return 1, True
        else:
            try:
                days = int(input("请输入天数 (默认7天): ") or "7")
                return days, False
            except:
                return 7, False

    def _crawl_with_dedup(self, days: int, only_today: bool) -> List[Dict]:
        """爬取并去重"""
        # 询问是否强制重新爬取
        print("\n去重选项:")
        print("1. 跳过已处理的文章（推荐）")
        print("2. 强制重新爬取所有文章")
        dedup_choice = input("请选择 (1/2，默认1): ").strip() or "1"

        force_crawl = (dedup_choice == "2")

        new_articles = []
        skipped_count = 0

        # 获取所有文章
        raw_articles = self.batch_crawler.crawl_all_accounts_with_return(days=days)

        # 过滤和去重
        today = date.today().isoformat()

        for article in raw_articles:
            # 如果只爬今天的，检查日期
            if only_today:
                article_date = self.data_processor.parse_date(article['date'])
                if article_date != today:
                    continue

            # 检查是否已处理（除非强制爬取）
            if not force_crawl and self.cache_manager.is_article_processed(
                    article['title'],
                    article['institution'],
                    article['date']
            ):
                skipped_count += 1
                continue

            new_articles.append(article)

            # 标记为已处理
            self.cache_manager.mark_article_processed(
                article['title'],
                article['institution'],
                article['date']
            )

        self.logger.info(f"文章统计: 总计{len(raw_articles)}篇，新文章{len(new_articles)}篇，跳过{skipped_count}篇")

        return new_articles

    def fetch_article_content(self, url: str, institution: str = "",
                              date: str = "", title: str = "") -> str:
        """获取文章内容"""
        # 先检查缓存
        cached_content = self.cache_manager.get_cached_content(url)
        if cached_content:
            self.logger.info("使用缓存内容")
            return cached_content

        # 获取新内容
        content = ""
        fetched_title = ""

        try:
            if self.wechat_crawler.is_valid_url(url):
                self.logger.info("使用微信爬虫获取内容")
                content, fetched_title = self.wechat_crawler.fetch_content(url)
            else:
                self.logger.info("使用Jina爬虫获取内容")
                content, fetched_title = self.jina_crawler.fetch_content(url)

            # 保存到缓存
            if content and len(content) > 100:
                if not title and fetched_title:
                    title = fetched_title

                self.cache_manager.save_article_with_auto_classify(
                    url, institution, date, title, content
                )

        except Exception as e:
            self.logger.error(f"获取内容失败: {e}")

        return content

    # 删除重复的 fetch_and_save_article 方法
