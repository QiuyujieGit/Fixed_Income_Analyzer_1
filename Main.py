"""主程序入口 - 简化版"""
import sys
from datetime import datetime
import os
from config.setting import setup_environment
from crawler.crawler_manager import CrawlerManager
from analyzer.analysis_manager import AnalysisManager
from report.report_manager import ReportManager
from utils.logger import setup_logger
from utils.cache_manager import CacheManager


class BondMarketAnalysisSystem:
    """债券市场分析系统 - 简化版"""

    def __init__(self):
        # 先设置环境，确保目录存在
        setup_environment()

        # 然后初始化日志
        self.logger = setup_logger("BondAnalyzer")
        self.logger.info("=" * 80)
        self.logger.info("初始化债券市场分析系统 - AI增强版")
        self.logger.info("=" * 80)

        try:
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

        # 爬取文章（只负责爬取，不负责筛选）
        new_articles = self.crawler_manager.crawl_articles()

        articles_to_analyze = []

        # 无论是否有新文章，都询问用户
        if new_articles:
            self.logger.info(f"发现 {len(new_articles)} 篇新文章")
            print(f"\n发现 {len(new_articles)} 篇新文章。")
            print("是否立即分析这些新文章？")
            choice = input("请选择 (y/n): ")

            if choice.lower() == 'y':
                articles_to_analyze = self.cache_manager._select_articles_for_analysis(new_articles)
            else:
                print("\n是否要分析今天所有的缓存文章（包括之前爬取的）？")
                choice2 = input("请选择 (y/n): ")
                if choice2.lower() == 'y':
                    articles_to_analyze = self.cache_manager.get_today_articles_for_analysis()
        else:
            self.logger.warning("没有新文章需要分析")

            # 检查今天的缓存
            today_folder = datetime.now().strftime('%Y%m%d')
            cache_path = os.path.join('data', 'cache', today_folder)

            if os.path.exists(cache_path):
                # 统计今天的缓存文章数
                total_cached = 0
                for type_folder in ['固收类', '权益类', '宏观类', '其他']:
                    type_path = os.path.join(cache_path, type_folder)
                    if os.path.exists(type_path):
                        total_cached += len([f for f in os.listdir(type_path) if f.endswith('.txt')])

                if total_cached > 0:
                    print(f"\n没有发现新文章，但今天的缓存中有 {total_cached} 篇文章。")
                    print("是否要分析今天的缓存文章？")
                    choice = input("请选择 (y/n): ")

                    if choice.lower() == 'y':
                        articles_to_analyze = self.cache_manager.get_today_articles_for_analysis()
                        if not articles_to_analyze:
                            self.logger.info("没有可分析的缓存文章")
                            return
                else:
                    print("\n今天没有任何缓存文章。")
                    return
            else:
                print("\n今天没有缓存文件夹。")
                return

        # 分析文章 - 只保留一次！
        if articles_to_analyze:
            self.logger.info(f"开始分析 {len(articles_to_analyze)} 篇文章...")
            analyses = self.analysis_manager.analyze_articles(articles_to_analyze)

            # 生成报告
            if analyses:
                self.report_manager.generate_reports(analyses)
            else:
                self.logger.warning("分析结果为空，无法生成报告")
        else:
            self.logger.info("没有选择要分析的文章")
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
