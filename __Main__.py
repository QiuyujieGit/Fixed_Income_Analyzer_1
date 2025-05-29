"""主程序入口"""
import sys
import time
import logging
from datetime import datetime

from config.setting import DEEPSEEK_API_KEY
from crawler.wechat_crawler import WechatCrawler
from crawler.jina_crawler import JinaCrawler
from analyzer.article_analyzer import ArticleAnalyzer
from analyzer.market_analyzer import MarketAnalyzer
from api.deepseek_client import DeepSeekClient
from report.excel_generator import ExcelGenerator
from report.text_generator import TextGenerator
from utils.file_handler import FileHandler
from utils.logger import setup_logger


class BondMarketAnalysisSystem:
    """债券市场分析系统"""

    def __init__(self):
        self.logger = setup_logger("BondAnalyzer")
        self.logger.info("初始化债券市场分析系统")

        # 初始化组件
        self.deepseek_client = DeepSeekClient()
        self.wechat_crawler = WechatCrawler()
        self.jina_crawler = JinaCrawler()
        self.article_analyzer = ArticleAnalyzer(self.deepseek_client)
        self.market_analyzer = MarketAnalyzer(self.deepseek_client)
        self.file_handler = FileHandler()
        self.excel_generator = ExcelGenerator()
        self.text_generator = TextGenerator()

    def run(self, excel_file: str):
        """运行分析"""
        start_time = datetime.now()
        self.logger.info("=" * 80)
        self.logger.info("债券市场观点自动化分析系统 - 开始运行")
        self.logger.info(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 80)

        # 1. 读取链接
        links, institutions, dates, pre_contents = self.file_handler.read_excel_links(excel_file)

        if not links:
            self.logger.error("未找到任何链接，分析终止")
            return

        # 2. 分析文章
        all_analyses = []
        for i, (link, inst, date, pre_content) in enumerate(zip(links, institutions, dates, pre_contents), 1):
            self.logger.info(f"\n[{i}/{len(links)}] 分析 {inst} 的文章")

            try:
                # 获取内容
                if pre_content and str(pre_content) != 'nan':
                    content = str(pre_content)
                else:
                    content = self._fetch_article_content(link)

                if not content:
                    continue

                # 分析文章
                analysis = self.article_analyzer.analyze(content, link, inst, str(date))
                all_analyses.append(analysis)

                self.logger.info(f"分析完成 - 评分: {analysis.get('重要性评分')}")

            except Exception as e:
                self.logger.error(f"处理文章失败: {e}")

            time.sleep(3)  # 避免请求过快

        # 3. 生成报告
        if all_analyses:
            self._generate_reports(all_analyses)

        # 完成
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"\n分析完成！总耗时: {duration:.2f} 秒")

    def _fetch_article_content(self, url: str) -> str:
        """获取文章内容"""
        # 先检查缓存
        cached_content = self.file_handler.check_cache(url)
        if cached_content:
            self.logger.info("使用缓存内容")
            return cached_content

        # 根据URL类型选择爬虫
        if self.wechat_crawler.is_valid_url(url):
            content, title = self.wechat_crawler.fetch_content(url)
        else:
            content, title = self.jina_crawler.fetch_content(url)

        # 保存缓存
        if content:
            cache_path = self.file_handler.get_cache_path(url, "", "", title)
            self.file_handler.save_cache(content, cache_path)

        return content

    def _generate_reports(self, analyses: list):
        """生成报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 生成Excel
        excel_path = self.excel_generator.generate(analyses, timestamp)
        self.logger.info(f"Excel报告已生成: {excel_path}")

        # 生成文本报告
        summary = self.market_analyzer.generate_summary(analyses)
        text_path = self.text_generator.generate(summary, timestamp)
        self.logger.info(f"文本报告已生成: {text_path}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        excel_file = "利率债市场观点建模.xlsx"
    else:
        excel_file = sys.argv[1]

    system = BondMarketAnalysisSystem()
    system.run(excel_file)


if __name__ == "__main__":
    main()