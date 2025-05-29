"""批量爬取脚本"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.wechat_batch_crawler import WechatBatchCrawler
from utils.logger import setup_logger


def main():
    """批量爬取主函数"""
    logger = setup_logger("BatchCrawl")

    print("=" * 80)
    print("微信公众号批量爬取系统")
    print("=" * 80)

    crawler = WechatBatchCrawler()

    # 加载公众号列表
    if not crawler.load_accounts():
        logger.error("加载公众号列表失败")
        return

    # 获取爬取天数
    try:
        days = int(input("请输入要爬取的天数（默认7天）: ") or "7")
    except ValueError:
        days = 7

    # 开始爬取
    crawler.crawl_all_accounts(days=days)

    print("\n批量爬取完成！")


if __name__ == "__main__":
    main()