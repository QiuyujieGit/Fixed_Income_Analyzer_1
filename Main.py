"""主程序入口 - 简化版"""
import sys
import os
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

            # 询问是否分析历史文章
            print("\n没有发现新文章。")
            print("是否要分析今天已爬取的历史文章？")
            choice = input("请选择 (y/n): ")

            if choice.lower() == 'y':
                # 获取今天的缓存文章
                articles = self._get_today_cached_articles()
                if not articles:
                    self.logger.info("今天没有缓存的文章")
                    return
            else:
                self.logger.info("退出爬取模式")
            return
        return

        # 分析文章
        analyses = self.analysis_manager.analyze_articles(articles)

        # 生成报告
        if analyses:
            self.report_manager.generate_reports(analyses)

    def _get_today_cached_articles(self) -> list:
        """获取今天缓存的文章"""
        today_folder = datetime.now().strftime('%Y%m%d')
        cache_path = os.path.join('data', 'cache', today_folder)

        if not os.path.exists(cache_path):
            return []

        articles = []

        # 遍历所有类型文件夹
        for type_folder in ['固收类', '权益类', '宏观类', '其他']:
            type_path = os.path.join(cache_path, type_folder)
            if not os.path.exists(type_path):
                continue

            for file_name in os.listdir(type_path):
                if file_name.endswith('.txt'):
                    file_path = os.path.join(type_path, file_name)

                    # 解析文件内容获取文章信息
                    article_info = self._parse_cached_article(file_path)
                    if article_info:
                        articles.append(article_info)

        self.logger.info(f"找到 {len(articles)} 篇今日缓存文章")
        return articles

    def _parse_cached_article(self, file_path: str) -> dict:
        """解析缓存的文章文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析文章信息
            article_info = {}
            lines = content.split('\n')

            for line in lines[:10]:  # 只解析前10行的元数据
                if line.startswith('标题:'):
                    article_info['title'] = line.replace('标题:', '').strip()
                elif line.startswith('机构:'):
                    article_info['institution'] = line.replace('机构:', '').strip()
                elif line.startswith('日期:'):
                    article_info['date'] = line.replace('日期:', '').strip()
                elif line.startswith('链接:'):
                    article_info['link'] = line.replace('链接:', '').strip()
                elif line.startswith('阅读数:'):
                    article_info['read_num'] = int(line.replace('阅读数:', '').strip() or '0')
                elif line.startswith('-' * 80):
                    break

            # 获取正文内容
            content_start = content.find('-' * 80)
            if content_start > 0:
                article_info['content'] = content[content_start + 81:].strip()

            # 从文件名推断文章类型
            file_name = os.path.basename(file_path)
            parent_folder = os.path.basename(os.path.dirname(file_path))
            article_info['article_type'] = parent_folder

            return article_info

        except Exception as e:
            self.logger.error(f"解析缓存文章失败: {e}")
            return None

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
