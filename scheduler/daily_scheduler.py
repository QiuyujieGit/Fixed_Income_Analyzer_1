"""定时任务调度器"""
import schedule
import time
import logging
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.wechat_batch_crawler import WechatBatchCrawler
from Main import BondMarketAnalysisSystem
from utils.logger import setup_logger


class DailyScheduler:
    """每日定时任务调度器"""

    def __init__(self):
        self.logger = setup_logger("DailyScheduler")
        self.batch_crawler = WechatBatchCrawler()

    def daily_crawl_task(self):
        """每日爬取任务"""
        self.logger.info("=" * 80)
        self.logger.info(f"开始执行每日爬取任务 - {datetime.now()}")
        self.logger.info("=" * 80)

        try:
            # 加载公众号列表
            if self.batch_crawler.load_accounts():
                # 爬取最新文章
                self.batch_crawler.crawl_all_accounts(days=1)

                # 生成分析报告
                self._generate_daily_report()

                self.logger.info("每日爬取任务完成")
            else:
                self.logger.error("加载公众号列表失败")

        except Exception as e:
            self.logger.error(f"每日爬取任务失败: {e}")

    def _generate_daily_report(self):
        """生成每日分析报告"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            cache_dir = os.path.join('data', 'cache')

            # 收集今天的文章
            articles_data = []

            for root, dirs, files in os.walk(cache_dir):
                for file in files:
                    if file.endswith('.txt') and today in file:
                        filepath = os.path.join(root, file)
                        # 解析文件获取元数据
                        metadata = self._parse_article_metadata(filepath)
                        if metadata:
                            articles_data.append(metadata)

            if articles_data:
                self.logger.info(f"找到 {len(articles_data)} 篇今日文章")

                # 创建临时Excel
                import pandas as pd
                df = pd.DataFrame(articles_data)

                temp_file = f'daily_articles_{today}.xlsx'
                temp_path = os.path.join('data', 'input', temp_file)
                df.to_excel(temp_path, index=False)

                # 运行分析
                system = BondMarketAnalysisSystem()
                system.run(temp_file)

                # 清理
                os.remove(temp_path)

        except Exception as e:
            self.logger.error(f"生成每日报告失败: {e}")

    def _parse_article_metadata(self, filepath: str) -> dict:
        """解析文章元数据"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            metadata = {}
            for line in lines[:10]:  # 只读前10行
                if line.startswith('链接:'):
                    metadata['链接'] = line.replace('链接:', '').strip()
                elif line.startswith('机构:'):
                    metadata['撰写机构'] = line.replace('机构:', '').strip()
                elif line.startswith('日期:'):
                    metadata['发布日期'] = line.replace('日期:', '').strip()
                elif line.startswith('阅读数:'):
                    metadata['阅读数'] = int(line.replace('阅读数:', '').strip() or '0')

            # 获取文章内容
            content_start = False
            content = []
            for line in lines:
                if content_start:
                    content.append(line)
                elif line.startswith('-' * 80):
                    content_start = True

            metadata['文章内容'] = ''.join(content)

            return metadata if '链接' in metadata else None

        except Exception as e:
            self.logger.error(f"解析文章失败: {e}")
            return None

    def run(self):
        """运行调度器"""
        # 设置定时任务
        schedule.every().day.at("08:00").do(self.daily_crawl_task)
        schedule.every().day.at("14:00").do(self.daily_crawl_task)  # 下午再跑一次

        self.logger.info("定时任务调度器已启动")
        self.logger.info("计划任务: 每天 08:00 和 14:00 执行")

        while True:
            schedule.run_pending()
            time.sleep(60)


if __name__ == "__main__":
    scheduler = DailyScheduler()

    print("\n选择运行模式:")
    print("1. 立即执行一次")
    print("2. 启动定时任务")

    choice = input("请选择 (1/2): ")

    if choice == '1':
        scheduler.daily_crawl_task()
    else:
        scheduler.run()