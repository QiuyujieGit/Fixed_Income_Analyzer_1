"""主程序入口 - 简化版"""
import sys
from datetime import datetime
from config.setting import setup_environment
from crawler.crawler_manager import CrawlerManager
from analyzer.analysis_manager import AnalysisManager
from report.report_manager import ReportManager
from utils.logger import setup_logger
from utils.cache_manager import CacheManager


class BondMarketAnalysisSystem:
    """债券市场分析系统 - 简化版"""

    def __init__(self):
        self.logger = setup_logger("BondAnalyzer")
        self.logger.info("=" * 80)
        self.logger.info("初始化债券市场分析系统 - AI增强版")
        self.logger.info("=" * 80)

        try:
            # 设置环境
            setup_environment()

            # 初始化各个管理器
            self.cache_manager = CacheManager()
            self.crawler_manager = CrawlerManager()
            self.analysis_manager = AnalysisManager()
            self.report_manager = ReportManager()

            # 清理旧缓存
            self.cache_manager.clean_old_cache(days_to_keep=7)

            self.logger.info("=" * 80)
            self.logger.info("所有组件初始化成功！")
            self.logger.info("=" * 80)

        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            raise

    def run(self, mode: str = None):
        """运行分析系统"""
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

        # 计算运行时间
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info(f"分析完成！总耗时: {duration:.2f} 秒 ({duration / 60:.1f} 分钟)")
        self.logger.info(f"{'=' * 80}")

    def _select_mode(self) -> str:
        """选择运行模式"""
        print("\n" + "=" * 80)
        print("债券市场观点自动化分析系统 - AI增强版")
        print("=" * 80)
        print("\n请选择运行模式:")
        print("1. 爬取公众号模式 - 从33个公众号爬取最新文章并分析")
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
        self.logger.info("\n运行模式: 爬取公众号")

        # 爬取文章
        articles = self.crawler_manager.crawl_articles()
        if not articles:
            self.logger.warning("没有新文章需要分析")
            return

        # 分析文章
        analyses = self.analysis_manager.analyze_articles(articles)

        # 生成报告
        if analyses:
            self.report_manager.generate_reports(analyses)

    def _run_excel_mode(self):
        """运行Excel链接模式"""
        self.logger.info("\n运行模式: Excel链接分析")

        # 获取Excel文件名
        excel_file = input("\n请输入Excel文件名（默认: 利率债市场观点建模.xlsx）: ")
        if not excel_file:
            excel_file = "利率债市场观点建模.xlsx"

        # 分析Excel中的链接
        analyses = self.analysis_manager.analyze_from_excel(excel_file)

        # 生成报告
        if analyses:
            self.report_manager.generate_reports(analyses)


def main():
    """主函数"""
    try:
        print("\n正在启动债券市场分析系统...")
        system = BondMarketAnalysisSystem()

        # 检查命令行参数
        if len(sys.argv) > 1:
            if sys.argv[1] == '--crawl':
                system.run(mode='crawl')
            elif sys.argv[1] == '--excel':
                system.run(mode='excel')
            elif sys.argv[1] == '--help':
                print("\n使用方法:")
                print("  python Main.py              # 交互式选择模式")
                print("  python Main.py --crawl      # 爬取公众号模式")
                print("  python Main.py --excel      # Excel链接模式")
            else:
                print(f"未知参数: {sys.argv[1]}")
        else:
            system.run()

    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
