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
from utils.data_processor import DataProcessor


class BondMarketAnalysisSystem:
    """债券市场分析系统"""

    def __init__(self):
        self.logger = setup_logger("BondAnalyzer")
        self.logger.info("=" * 80)
        self.logger.info("初始化债券市场分析系统")
        self.logger.info("=" * 80)

        try:
            # 初始化组件
            self.deepseek_client = DeepSeekClient()
            self.wechat_crawler = WechatCrawler()
            self.jina_crawler = JinaCrawler()
            self.article_analyzer = ArticleAnalyzer(self.deepseek_client)
            self.market_analyzer = MarketAnalyzer(self.deepseek_client)
            self.file_handler = FileHandler()
            self.excel_generator = ExcelGenerator()
            self.text_generator = TextGenerator()
            self.data_processor = DataProcessor()

            self.logger.info("所有组件初始化成功")
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            raise

    def run(self, excel_file: str):
        """运行分析"""
        start_time = datetime.now()
        self.logger.info("=" * 80)
        self.logger.info("债券市场观点自动化分析系统 - 开始运行")
        self.logger.info(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"输入文件: {excel_file}")
        self.logger.info("=" * 80)

        # 读取链接
        try:
            links, institutions, dates, pre_contents = self.file_handler.read_excel_links(excel_file)
        except FileNotFoundError as e:
            self.logger.error(f"文件未找到: {e}")
            self.logger.error(f"请确保文件位于 data/input/ 目录下")
            return
        except Exception as e:
            self.logger.error(f"读取文件失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return

        if not links:
            self.logger.error("未找到任何链接，分析终止")
            return

        # 统计信息
        self.logger.info(f"读取到 {len(links)} 个链接")
        wechat_count = sum(1 for url in links if "mp.weixin.qq.com" in url)
        if wechat_count > 0:
            self.logger.info(f"其中包含 {wechat_count} 篇微信公众号文章")

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
                    self.logger.warning("文章内容过短或为空，跳过该文章")
                    failed_count += 1
                    continue

                # 清理内容
                content = self.data_processor.clean_text(content)

                # 分析文章
                analysis = self.article_analyzer.analyze(content, link, inst, str(date))

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
                import traceback
                self.logger.error(traceback.format_exc())
                failed_count += 1

            # 避免请求过快
            if i < len(links):
                self.logger.info("等待3秒后继续...")
                time.sleep(3)

        # 输出统计
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info("文章分析完成统计:")
        self.logger.info(f"- 成功: {successful_count}")
        self.logger.info(f"- 失败: {failed_count}")
        self.logger.info(f"- 总计: {len(links)}")
        self.logger.info(f"- 成功率: {successful_count / len(links) * 100:.1f}%")

        # 生成报告
        if all_analyses:
            self._generate_reports(all_analyses)
        else:
            self.logger.error("没有成功分析的文章，无法生成报告")

        # 完成
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info(f"分析完成！")
        self.logger.info(f"总耗时: {duration:.2f} 秒 ({duration / 60:.1f} 分钟)")
        self.logger.info(f"{'=' * 80}")

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
            import traceback
            self.logger.error(traceback.format_exc())


def main():
    """主函数"""
    print("\n债券市场观点自动化分析系统 v1.0")
    print("=" * 50)

    # 检查命令行参数
    if len(sys.argv) < 2:
        excel_file = "利率债市场观点建模.xlsx"
        print(f"未指定文件，使用默认文件: {excel_file}")
    else:
        excel_file = sys.argv[1]

    # 创建并运行系统
    try:
        system = BondMarketAnalysisSystem()
        system.run(excel_file)
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
