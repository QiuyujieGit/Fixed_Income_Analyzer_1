"""爬虫管理器 - 统一管理所有爬虫功能"""
import os
from datetime import datetime, date
from typing import List, Dict
from .wechat_batch_crawler import WechatBatchCrawler
from .wechat_crawler import WechatCrawler
from .jina_crawler import JinaCrawler
from utils.logger import setup_logger
from utils.article_classifier import ArticleClassifier
from utils.cache_manager import CacheManager
from utils.data_processor import DataProcessor


class CrawlerManager:
    """爬虫管理器"""

    def __init__(self):
        self.logger = setup_logger("CrawlerManager")
        self.batch_crawler = WechatBatchCrawler()
        self.wechat_crawler = WechatCrawler()
        self.jina_crawler = JinaCrawler()
        self.article_classifier = ArticleClassifier()
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

        if not articles:
            return []

        # 显示缓存统计
        self._show_cache_statistics()

        # 文章分类和筛选
        filtered_articles = self._classify_and_filter_articles(articles)

        return filtered_articles

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

            # 检查是否已处理
            if self.cache_manager.is_article_processed(
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

    def _classify_and_filter_articles(self, articles: List[Dict]) -> List[Dict]:
        """分类和筛选文章"""
        # 分类文章
        classified_articles = self.article_classifier.classify_batch(articles)

        # 显示分类统计
        self._show_classification_stats(classified_articles)

        # 让用户选择分析模式
        analysis_mode = self._select_analysis_mode()

        # 根据选择筛选文章
        if analysis_mode == 'bond_only':
            filtered_articles = classified_articles.get('固收类', [])
            self.logger.info(f"仅分析固收类文章：{len(filtered_articles)}篇")
        elif analysis_mode == 'bond_macro':
            filtered_articles = (classified_articles.get('固收类', []) +
                                 classified_articles.get('宏观类', []))
            self.logger.info(f"分析固收和宏观类文章：{len(filtered_articles)}篇")
        else:
            filtered_articles = articles
            self.logger.info(f"分析所有文章：{len(filtered_articles)}篇")

        return filtered_articles

    def _show_classification_stats(self, classified_articles: dict):
        """显示分类统计"""
        print("\n" + "=" * 60)
        print("文章分类统计")
        print("=" * 60)

        total = sum(len(articles) for articles in classified_articles.values())

        for category, articles in classified_articles.items():
            count = len(articles)
            percentage = (count / total * 100) if total > 0 else 0
            print(f"{category}: {count}篇 ({percentage:.1f}%)")

            if articles and count > 0:
                print(f"  示例文章:")
                for i, article in enumerate(articles[:3]):
                    title = article.get('title', '未知标题')
                    if len(title) > 50:
                        title = title[:50] + "..."
                    print(f"    {i + 1}. {title}")
                if count > 3:
                    print(f"    ... 还有{count - 3}篇")

        print("=" * 60)

    def _select_analysis_mode(self) -> str:
        """选择分析模式"""
        print("\n请选择分析模式:")
        print("1. 仅分析固收类文章（推荐）")
        print("2. 分析固收和宏观类文章")
        print("3. 分析所有文章")
        print("-" * 40)

        while True:
            choice = input("请选择 (1/2/3，默认1): ").strip() or "1"
            if choice == '1':
                return 'bond_only'
            elif choice == '2':
                return 'bond_macro'
            elif choice == '3':
                return 'all'
            else:
                print("无效选择，请重新输入")

    def _show_cache_statistics(self):
        """显示缓存统计信息"""
        today_folder = datetime.now().strftime('%Y%m%d')
        stats = self.cache_manager.get_cache_statistics(today_folder)

        print("\n" + "=" * 60)
        print(f"今日缓存统计 ({today_folder})")
        print("=" * 60)
        for category, count in stats.items():
            if category != '总计':
                print(f"{category}: {count}篇")
        print("-" * 60)
        print(f"总计: {stats['总计']}篇")
        print("=" * 60)

    def fetch_article_content(self, url: str, institution: str = "",
                              date: str = "", title: str = "") -> str:
        """获取文章内容"""
        # 先检查缓存
        today_folder = datetime.now().strftime('%Y%m%d')
        cached_content = self.cache_manager.check_cache(url, today_folder)

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

            # 保存缓存
            if content and len(content) > 100:
                if not title and fetched_title:
                    title = fetched_title

                parsed_date = self.data_processor.parse_date(date)
                article_type = self.article_classifier.classify(title, institution, content[:500])

                self.cache_manager.save_article_cache(
                    url, institution, parsed_date, title, article_type, content
                )

        except Exception as e:
            self.logger.error(f"获取内容失败: {e}")

        return content