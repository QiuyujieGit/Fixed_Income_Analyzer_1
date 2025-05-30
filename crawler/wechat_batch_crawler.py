"""批量微信公众号爬虫"""
import os
import time
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd
import requests
from lxml import etree
import logging

from config.setting import INPUT_DIR, CACHE_DIR
from .wechat_crawler import WechatCrawler
from utils.file_handler import FileHandler
from utils.article_classifier import ArticleClassifier


class WechatBatchCrawler(WechatCrawler):
    """批量爬取多个微信公众号"""

    def __init__(self):
        super().__init__()
        self.accounts_info = {}
        self.search_url = "https://mp.weixin.qq.com/cgi-bin/searchbiz"
        self.article_list_url = "https://mp.weixin.qq.com/cgi-bin/appmsg"
        # 使用统一的分类器
        self.article_classifier = ArticleClassifier()

    # 删除第一个重复的 is_relevant_article 方法

    def load_accounts(self, excel_file: str = "主要公众号来源.xlsx"):
        """加载公众号列表"""
        file_path = os.path.join(INPUT_DIR, excel_file)

        try:
            df = pd.read_excel(file_path)
            self.logger.info(f"加载了 {len(df)} 个公众号")

            for _, row in df.iterrows():
                account_name = row['公众号名称']
                self.accounts_info[account_name] = {
                    '撰写机构': row['撰写机构'],
                    '机构分类': row['机构分类'],
                    '内容分类': row['内容分类'],
                    'fakeid': None
                }

            # 加载已保存的fakeid
            self._load_saved_fakeids()
            return True

        except Exception as e:
            self.logger.error(f"加载公众号列表失败: {e}")
            return False

    def _load_saved_fakeids(self):
        """加载已保存的fakeid"""
        cache_file = os.path.join(CACHE_DIR, 'accounts_fakeid.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    saved_fakeids = json.load(f)

                for account_name, fakeid in saved_fakeids.items():
                    if account_name in self.accounts_info:
                        self.accounts_info[account_name]['fakeid'] = fakeid

                self.logger.info(f"加载了 {len(saved_fakeids)} 个已保存的fakeid")
            except Exception as e:
                self.logger.error(f"加载fakeid失败: {e}")

    def _save_fakeids(self):
        """保存fakeid"""
        cache_file = os.path.join(CACHE_DIR, 'accounts_fakeid.json')
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)

        fakeids = {
            name: info['fakeid']
            for name, info in self.accounts_info.items()
            if info['fakeid']
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(fakeids, f, ensure_ascii=False, indent=2)

    def search_account(self, account_name: str) -> str:
        """搜索公众号获取fakeid"""
        if not self.token:
            self.logger.error("未登录，请先登录")
            return ""

        params = {
            'action': 'search_biz',
            'begin': '0',
            'count': '5',
            'query': account_name,
            'token': self.token,
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1'
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://mp.weixin.qq.com/',
            'Cookie': self.cookie
        }

        try:
            response = self.session.get(self.search_url, params=params, headers=headers)
            data = response.json()

            if data.get('base_resp', {}).get('ret') == 0:
                biz_list = data.get('list', [])
                if biz_list:
                    # 优先完全匹配
                    for biz in biz_list:
                        if biz.get('nickname') == account_name:
                            return biz.get('fakeid')

                    # 返回第一个结果
                    return biz_list[0].get('fakeid')
            else:
                self.logger.error(f"搜索失败: {data.get('base_resp', {}).get('err_msg')}")

        except Exception as e:
            self.logger.error(f"搜索公众号 {account_name} 失败: {e}")

        return ""

    def get_recent_articles(self, fakeid: str, account_name: str, days: int = 7) -> List[Dict]:
        """获取公众号最近的文章列表"""
        if not self.token:
            return []

        articles = []
        begin = 0
        count = 10

        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        while True:
            params = {
                'action': 'list_ex',
                'begin': str(begin),
                'count': str(count),
                'fakeid': fakeid,
                'type': '9',
                'query': '',
                'token': self.token,
                'lang': 'zh_CN',
                'f': 'json',
                'ajax': '1'
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://mp.weixin.qq.com/',
                'Cookie': self.cookie
            }

            try:
                response = self.session.get(self.article_list_url, params=params, headers=headers)
                data = response.json()

                if data.get('base_resp', {}).get('ret') == 0:
                    app_msg_list = data.get('app_msg_list', [])

                    if not app_msg_list:
                        break

                    for item in app_msg_list:
                        create_time = item.get('create_time', 0)
                        if create_time:
                            article_time = datetime.fromtimestamp(create_time)

                            if article_time < start_time:
                                return articles

                            if article_time <= end_time:
                                articles.append({
                                    'title': item.get('title', ''),
                                    'link': item.get('link', ''),
                                    'digest': item.get('digest', ''),
                                    'create_time': article_time.strftime('%Y-%m-%d'),
                                    'cover': item.get('cover', ''),
                                    'account_name': account_name,
                                    'read_num': item.get('read_num', 0),  # 阅读数
                                    'like_num': item.get('like_num', 0)   # 点赞数
                                })

                    begin += count
                    time.sleep(2)

                else:
                    self.logger.error(f"获取文章列表失败: {data.get('base_resp', {}).get('err_msg')}")
                    break

            except Exception as e:
                self.logger.error(f"获取公众号 {account_name} 文章列表失败: {e}")
                break

        return articles

    # 删除重复的 is_relevant_article 方法，直接使用 article_classifier 的方法

    def fetch_and_save_article(self, article_info: Dict, account_info: Dict) -> bool:
        """获取并保存文章内容"""
        try:
            # 获取文章内容
            content, _ = self.fetch_content(article_info['link'])

            if not content or len(content) < 100:
                self.logger.warning(f"文章内容过短或为空: {article_info['title']}")
                return False

            # 构建完整内容（包含元数据）
            full_content = f"""标题: {article_info['title']}
机构: {account_info['撰写机构']}
日期: {article_info['create_time']}
链接: {article_info['link']}
阅读数: {article_info.get('read_num', 0)}
{'-' * 80}

{content}"""

            # 使用统一的缓存管理器保存
            from utils.cache_manager import CacheManager
            from utils.data_processor import DataProcessor

            cache_manager = CacheManager()
            data_processor = DataProcessor()

            # 获取标准化日期
            parsed_date = data_processor.parse_date(article_info['create_time'])

            # 使用分类器确定文章类型
            article_type = self.article_classifier.classify(
                title=article_info['title'],
                institution=account_info['撰写机构'],
                content=content[:500],
                content_type=account_info['内容分类']
            )

            # 获取缓存路径
            cache_path = cache_manager.file_handler.get_cache_path(
                article_info['link'],
                account_info['撰写机构'],
                parsed_date,
                article_info['title'],
                article_type
            )

            # 保存完整内容
            cache_manager.file_handler.save_cache(full_content, cache_path)

            self.logger.info(f"文章已保存: {article_info['title']}")
            return True

        except Exception as e:
            self.logger.error(f"保存文章失败: {e}")
            return False

    def _fetch_and_save_article_with_return(self, article_info: Dict, account_info: Dict) -> str:
        """获取并保存文章内容，同时返回内容"""
        try:
            # 获取文章内容
            content, _ = self.fetch_content(article_info['link'])

            if not content or len(content) < 100:
                self.logger.warning(f"文章内容过短或为空: {article_info['title']}")
                return ""

            # 保存文章
            self.fetch_and_save_article(article_info, account_info)

            return content

        except Exception as e:
            self.logger.error(f"获取文章内容失败: {e}")
            return ""

    def crawl_all_accounts(self, days: int = 7):
        """爬取所有公众号的最新文章（原方法）"""
        if not self.accounts_info:
            self.logger.error("未加载公众号列表")
            return

        # 检查登录
        if not self.token:
            self.logger.info("需要登录微信公众平台")
            if not self.login():
                return

        # 统计
        total_accounts = len(self.accounts_info)
        success_count = 0
        article_count = 0

        self.logger.info(f"开始爬取 {total_accounts} 个公众号的最新文章")

        for i, (account_name, account_info) in enumerate(self.accounts_info.items(), 1):
            self.logger.info(f"\n[{i}/{total_accounts}] 处理公众号: {account_name}")

            try:
                # 获取或搜索fakeid
                fakeid = self._get_or_search_fakeid(account_name, account_info)
                if not fakeid:
                    continue

                # 获取文章
                articles = self.get_recent_articles(fakeid, account_name, days)
                self.logger.info(f"获取到 {len(articles)} 篇文章")

                # 筛选相关文章并保存
                article_count += self._filter_and_save_articles(articles, account_info)

                success_count += 1
                time.sleep(3)

            except Exception as e:
                self.logger.error(f"处理公众号 {account_name} 失败: {e}")

        # 输出统计
        self.logger.info(f"\n爬取完成统计:")
        self.logger.info(f"- 成功处理公众号: {success_count}/{total_accounts}")
        self.logger.info(f"- 获取文章总数: {article_count}")

    def crawl_all_accounts_with_return(self, days: int = 7) -> list:
        """爬取所有公众号并返回文章信息（新方法）"""
        if not self.accounts_info:
            self.logger.error("未加载公众号列表")
            return []

        # 检查登录
        if not self.token:
            self.logger.info("需要登录微信公众平台")
            if not self.login():
                return []

        # 统计
        total_accounts = len(self.accounts_info)
        success_count = 0
        all_articles = []  # 存储所有爬取的文章信息

        self.logger.info(f"开始爬取 {total_accounts} 个公众号的最新文章")

        for i, (account_name, account_info) in enumerate(self.accounts_info.items(), 1):
            self.logger.info(f"\n[{i}/{total_accounts}] 处理公众号: {account_name}")

            try:
                # 获取或搜索fakeid
                fakeid = self._get_or_search_fakeid(account_name, account_info)
                if not fakeid:
                    continue

                # 获取文章列表
                articles = self.get_recent_articles(fakeid, account_name, days)
                self.logger.info(f"获取到 {len(articles)} 篇文章")

                # 筛选并处理文章
                processed_articles = self._filter_and_process_articles(articles, account_info)
                all_articles.extend(processed_articles)

                success_count += 1
                time.sleep(3)

            except Exception as e:
                self.logger.error(f"处理公众号 {account_name} 失败: {e}")

        # 输出统计
        self.logger.info(f"\n爬取完成统计:")
        self.logger.info(f"- 成功处理公众号: {success_count}/{total_accounts}")
        self.logger.info(f"- 获取文章总数: {len(all_articles)}")

        return all_articles

    # 新增辅助方法，减少重复代码
    def _get_or_search_fakeid(self, account_name: str, account_info: Dict) -> str:
        """获取或搜索fakeid"""
        if not account_info['fakeid']:
            fakeid = self.search_account(account_name)
            if fakeid:
                account_info['fakeid'] = fakeid
                self.accounts_info[account_name]['fakeid'] = fakeid
                self._save_fakeids()
            else:
                self.logger.warning(f"未找到公众号: {account_name}")
                return ""
        else:
            fakeid = account_info['fakeid']

        return fakeid

    def _filter_and_save_articles(self, articles: List[Dict], account_info: Dict) -> int:
        """筛选相关文章并保存，返回保存的文章数"""
        saved_count = 0

        for article in articles:
            # 使用统一的分类器判断文章是否相关
            if self.article_classifier.is_relevant_article(
                article['title'],
                article['digest'],
                account_info['内容分类']
            ):
                if self.fetch_and_save_article(article, account_info):
                    saved_count += 1

        self.logger.info(f"筛选并保存了 {saved_count} 篇相关文章")
        return saved_count

    def _filter_and_process_articles(self, articles: List[Dict], account_info: Dict) -> List[Dict]:
        """筛选并处理文章，返回处理后的文章列表"""
        processed_articles = []

        for article in articles:
            # 使用统一的分类器判断文章是否相关
            if self.article_classifier.is_relevant_article(
                article['title'],
                article['digest'],
                account_info['内容分类']
            ):
                # 获取并保存内容
                content = self._fetch_and_save_article_with_return(article, account_info)
                if content:
                    # 添加到返回列表
                    processed_articles.append({
                        'link': article['link'],
                        'institution': account_info['撰写机构'],
                        'date': article['create_time'],
                        'title': article['title'],
                        'content': content,
                        'read_num': article.get('read_num', 0),
                        'category': account_info['机构分类'],
                        'content_type': account_info['内容分类']
                    })

        self.logger.info(f"筛选出 {len(processed_articles)} 篇相关文章")
        return processed_articles
