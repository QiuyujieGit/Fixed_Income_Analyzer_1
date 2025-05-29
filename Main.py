"""主程序入口"""
import sys
import os
import hashlib
import time
import json
import logging
from datetime import datetime, date
import pandas as pd

from config.setting import DEEPSEEK_API_KEY
from crawler.wechat_crawler import WechatCrawler
from crawler.wechat_batch_crawler import WechatBatchCrawler
from crawler.jina_crawler import JinaCrawler
from analyzer.article_analyzer import ArticleAnalyzer
from analyzer.market_analyzer import MarketAnalyzer
from api.deepseek_client import DeepSeekClient
from report.excel_generator import ExcelGenerator
from report.text_generator import TextGenerator
from utils.file_handler import FileHandler
from utils.logger import setup_logger
from utils.data_processor import DataProcessor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class BondMarketAnalysisSystem:
    """债券市场分析系统 - 整合版"""

    def __init__(self):
        self.logger = setup_logger("BondAnalyzer")
        self.logger.info("=" * 80)
        self.logger.info("初始化债券市场分析系统")
        self.logger.info("=" * 80)

        try:
            # 初始化组件
            self.deepseek_client = DeepSeekClient()
            self.wechat_crawler = WechatCrawler()
            self.batch_crawler = WechatBatchCrawler()
            self.jina_crawler = JinaCrawler()
            self.article_analyzer = ArticleAnalyzer(self.deepseek_client)
            self.market_analyzer = MarketAnalyzer(self.deepseek_client)
            self.file_handler = FileHandler()
            self.excel_generator = ExcelGenerator()
            self.text_generator = TextGenerator()
            self.data_processor = DataProcessor()

            # 初始化去重系统
            self.hash_cache_file = os.path.join('data', 'cache', 'article_hashes.json')
            self.article_hashes = self._load_article_hashes()

            self.logger.info("所有组件初始化成功")
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            raise

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

    def _is_article_processed(self, title: str, institution: str, date: str) -> bool:
        """检查文章是否已处理"""
        article_hash = self._get_article_hash(title, institution, date)
        today = datetime.now().date().isoformat()

        if article_hash in self.article_hashes:
            # 检查是否是今天处理的
            processed_date = self.article_hashes[article_hash].get('processed_date')
            if processed_date == today:
                return True
        return False

    def _mark_article_processed(self, title: str, institution: str, date: str):
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

    def run(self, mode: str = None):
        """运行分析系统

        Args:
            mode: 运行模式，如果不指定则让用户选择
                 - 'crawl': 爬取公众号模式
                 - 'excel': Excel链接模式
        """
        start_time = datetime.now()

        # 选择运行模式
        if not mode:
            mode = self._select_mode()

        if mode == 'crawl':
            self._run_crawl_mode()
        elif mode == 'excel':
            self._run_excel_mode()
        else:
            self.logger.error("无效的运行模式")
            return

        # 完成
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info(f"分析完成！")
        self.logger.info(f"总耗时: {duration:.2f} 秒 ({duration / 60:.1f} 分钟)")
        self.logger.info(f"{'=' * 80}")

    def _select_mode(self) -> str:
        """选择运行模式"""
        print("\n" + "=" * 80)
        print("债券市场观点自动化分析系统")
        print("=" * 80)
        print("\n请选择运行模式:")
        print("1. 爬取公众号模式 - 从33个公众号爬取当日最新文章并分析")
        print("2. Excel链接模式 - 分析Excel文件中提供的文章链接")
        print("\n" + "-" * 80)

        while True:
            choice = input("\n请选择 (1/2): ")
            if choice == '1':
                return 'crawl'
            elif choice == '2':
                return 'excel'
            else:
                print("无效选择，请重新输入")

    def _run_crawl_mode(self):
        """运行爬取公众号模式"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("运行模式: 爬取公众号")
        self.logger.info("=" * 60)

        # 加载公众号列表
        if not self.batch_crawler.load_accounts():
            self.logger.error("加载公众号列表失败")
            return

        # 询问爬取选项
        print("\n爬取选项:")
        print("1. 只爬取今日文章（推荐）")
        print("2. 爬取最近N天文章")

        crawl_option = input("\n请选择 (1/2): ")

        if crawl_option == '1':
            days = 1
            only_today = True
        else:
            try:
                days = int(input("请输入天数: "))
                only_today = False
            except:
                days = 7
                only_today = False

        # 开始爬取
        self.logger.info(f"开始爬取最近{days}天的文章...")
        articles = self._crawl_with_dedup(days, only_today)

        if not articles:
            self.logger.warning("没有新文章需要分析")
            return

        # 分析文章
        self._analyze_crawled_articles(articles)

    def _crawl_with_dedup(self, days: int, only_today: bool) -> list:
        """爬取并去重"""
        all_articles = []
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
            if self._is_article_processed(
                    article['title'],
                    article['institution'],
                    article['date']
            ):
                skipped_count += 1
                self.logger.debug(f"跳过已处理文章: {article['title']}")
                continue

            new_articles.append(article)

            # 标记为已处理
            self._mark_article_processed(
                article['title'],
                article['institution'],
                article['date']
            )

        self.logger.info(f"文章统计: 总计{len(raw_articles)}篇，新文章{len(new_articles)}篇，跳过{skipped_count}篇")

        return new_articles

    def _analyze_crawled_articles(self, articles: list):
        """分析爬取的文章"""
        if not articles:
            return

        try:
            # 准备Excel数据
            excel_data = []
            for article in articles:
                excel_data.append({
                    '链接': article['link'],
                    '撰写机构': article['institution'],
                    '发布日期': article['date'],
                    '文章内容': article.get('content', ''),
                    '阅读数': article.get('read_num', 0)
                })

            # 创建临时文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_filename = f'crawled_articles_{timestamp}.xlsx'
            temp_path = os.path.join('data', 'input', temp_filename)

            df = pd.DataFrame(excel_data)
            df.to_excel(temp_path, index=False)

            self.logger.info(f"创建临时分析文件: {temp_filename}")

            # 运行分析
            self._run_analysis(temp_filename)

            # 清理
            if os.path.exists(temp_path):
                os.remove(temp_path)

        except Exception as e:
            self.logger.error(f"分析文章失败: {e}")

    def _run_excel_mode(self):
        """运行Excel链接模式"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("运行模式: Excel链接分析")
        self.logger.info("=" * 60)

        # 获取Excel文件名
        excel_file = input("\n请输入Excel文件名（默认: 利率债市场观点建模.xlsx）: ")
        if not excel_file:
            excel_file = "利率债市场观点建模.xlsx"

        # 运行分析
        self._run_analysis(excel_file)

    def _run_analysis(self, excel_file: str):
        """运行分析流程（共用部分）"""
        # 读取链接
        try:
            links, institutions, dates, pre_contents = self.file_handler.read_excel_links(excel_file)
        except FileNotFoundError as e:
            self.logger.error(f"文件未找到: {e}")
            return
        except Exception as e:
            self.logger.error(f"读取文件失败: {e}")
            return

        if not links:
            self.logger.error("未找到任何链接")
            return

        self.logger.info(f"读取到 {len(links)} 个链接")

        # 分析文章
        all_analyses = []
        successful_count = 0
        failed_count = 0

        for i, (link, inst, date, pre_content) in enumerate(zip(links, institutions, dates, pre_contents), 1):
            self.logger.info(f"\n{'=' * 60}")
            self.logger.info(f"[{i}/{len(links)}] 开始分析")
            self.logger.info(f"机构: {inst}")
            self.logger.info(f"日期: {self.data_processor.parse_date(date)}")
            self.logger.info(f"链接: {link}")

            try:
                # 获取内容
                if pre_content and str(pre_content) != 'nan' and len(str(pre_content)) > 100:
                    self.logger.info("使用Excel中预存的文章内容")
                    content = str(pre_content)
                else:
                    content = self._fetch_article_content(link, inst, date)

                if not content or len(content) < 100:
                    self.logger.warning("文章内容过短或为空，跳过")
                    failed_count += 1
                    continue

                # 清理内容
                content = self.data_processor.clean_text(content)

                # 分析文章
                analysis = self.article_analyzer.analyze(content, link, inst, str(date))

                # 增强评分（如果有阅读数）
                if hasattr(self, 'current_read_count'):
                    enhanced_score = self.data_processor.calculate_article_score(
                        analysis,
                        self.current_read_count
                    )
                    analysis.update(enhanced_score)

                # 验证分析结果
                if self.data_processor.validate_analysis_result(analysis):
                    all_analyses.append(analysis)
                    successful_count += 1
                    self.logger.info(f"分析完成 - 评分: {analysis.get('重要性评分')}")
                else:
                    self.logger.warning("分析结果验证失败")
                    failed_count += 1

            except Exception as e:
                self.logger.error(f"处理文章失败: {e}")
                failed_count += 1

            # 避免请求过快
            if i < len(links):
                time.sleep(3)

        # 输出统计
        self.logger.info(f"\n文章分析完成统计:")
        self.logger.info(f"- 成功: {successful_count}")
        self.logger.info(f"- 失败: {failed_count}")
        self.logger.info(f"- 成功率: {successful_count / len(links) * 100:.1f}%")

        # 生成报告
        if all_analyses:
            self._generate_reports(all_analyses)
        else:
            self.logger.error("没有成功分析的文章")

    def _fetch_article_content(self, url: str, institution: str = "", date: str = "") -> str:
        """获取文章内容"""
        # 先检查缓存
        cached_content = self.file_handler.check_cache(url)
        if cached_content:
            self.logger.info("使用缓存内容")
            return cached_content

        # 根据URL类型选择爬虫
        content = ""
        title = ""

        try:
            if self.wechat_crawler.is_valid_url(url):
                self.logger.info("使用微信爬虫获取内容")
                content, title = self.wechat_crawler.fetch_content(url)
            else:
                self.logger.info("使用Jina爬虫获取内容")
                content, title = self.jina_crawler.fetch_content(url)

            # 保存缓存
            if content and len(content) > 100:
                parsed_date = self.data_processor.parse_date(date)
                cache_path = self.file_handler.get_cache_path(url, institution, parsed_date, title)
                self.file_handler.save_cache(content, cache_path)
                self.logger.info(f"内容已缓存")
        except Exception as e:
            self.logger.error(f"获取内容失败: {e}")

        return content

    def _generate_reports(self, analyses: list):
        """生成报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        self.logger.info(f"\n{'=' * 60}")
        self.logger.info("开始生成分析报告...")

        # 生成统计信息
        metadata = self.data_processor.merge_analyses(analyses)
        self.logger.info(f"统计信息: {len(analyses)} 篇文章, 平均评分 {metadata['average_score']}")

        # 生成Excel
        try:
            excel_path = self.excel_generator.generate(analyses, timestamp)
            self.logger.info(f"✓ Excel报告已生成: {excel_path}")
        except Exception as e:
            self.logger.error(f"✗ 生成Excel失败: {e}")

        # 生成综合分析
        try:
            summary = self.market_analyzer.generate_summary(analyses)

            # 生成文本报告
            text_path = self.text_generator.generate(summary, timestamp, metadata)
            self.logger.info(f"✓ 文本报告已生成: {text_path}")

            # 在控制台显示报告
            print("\n" + "=" * 80)
            print("【债券市场观点总结报告】")
            print("=" * 80)
            print(summary)
            print("=" * 80)

        except Exception as e:
            self.logger.error(f"✗ 生成文本报告失败: {e}")


def main():
    """主函数"""
    try:
        system = BondMarketAnalysisSystem()

        # 检查命令行参数
        if len(sys.argv) > 1:
            if sys.argv[1] == '--crawl':
                system.run(mode='crawl')
            elif sys.argv[1] == '--excel':
                if len(sys.argv) > 2:
                    # 直接运行Excel模式
                    system._run_analysis(sys.argv[2])
                else:
                    system.run(mode='excel')
            else:
                print(f"未知参数: {sys.argv[1]}")
        else:
            # 交互式选择
            system.run()

    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
