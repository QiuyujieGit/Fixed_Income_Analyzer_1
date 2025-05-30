"""分析管理器 - 统一管理所有分析功能"""
import os
import time
import pandas as pd
from typing import List, Dict
from datetime import datetime
from .article_analyzer import ArticleAnalyzer
from .market_analyzer import MarketAnalyzer
from api.deepseek_client import DeepSeekClient
from crawler.crawler_manager import CrawlerManager
from utils.logger import setup_logger
from utils.data_processor import DataProcessor
from utils.file_handler import FileHandler


class AnalysisManager:
    """分析管理器"""

    def __init__(self):
        self.logger = setup_logger("AnalysisManager")
        self.deepseek_client = DeepSeekClient()
        self.article_analyzer = ArticleAnalyzer(self.deepseek_client)
        self.market_analyzer = MarketAnalyzer(self.deepseek_client)
        self.data_processor = DataProcessor(deepseek_client=self.deepseek_client)
        self.file_handler = FileHandler()
        self.crawler_manager = CrawlerManager()

    def analyze_articles(self, articles: List[Dict]) -> List[Dict]:
        """分析文章列表"""
        if not articles:
            return []

        # 预估分析时间
        estimated_time = len(articles) * 60
        self.logger.info(f"预计分析时间：约{estimated_time // 60}分钟")

        # 创建临时Excel文件
        temp_filename = self._create_temp_excel(articles)

        try:
            # 运行分析
            analyses = self._run_analysis(temp_filename, include_read_count=True)

            # 清理临时文件
            temp_path = os.path.join('data', 'input', temp_filename)
            if os.path.exists(temp_path):
                os.remove(temp_path)
                self.logger.info("临时文件已清理")

            return analyses

        except Exception as e:
            self.logger.error(f"分析文章失败: {e}")
            return []

    def analyze_from_excel(self, excel_file: str) -> List[Dict]:
        """从Excel文件分析"""
        return self._run_analysis(excel_file)

    def _create_temp_excel(self, articles: List[Dict]) -> str:
        """创建临时Excel文件"""
        excel_data = []
        for article in articles:
            excel_data.append({
                '链接': article['link'],
                '撰写机构': article['institution'],
                '发布日期': article['date'],
                '文章内容': article.get('content', ''),
                '阅读数': article.get('read_num', 0),
                '文章类型': article.get('article_type', '未分类'),
                '文章标题': article.get('title', '')
            })

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_filename = f'crawled_articles_{timestamp}.xlsx'
        temp_path = os.path.join('data', 'input', temp_filename)

        os.makedirs(os.path.dirname(temp_path), exist_ok=True)

        df = pd.DataFrame(excel_data)
        df.to_excel(temp_path, index=False)

        self.logger.info(f"创建临时分析文件: {temp_filename}")

        return temp_filename

    def _run_analysis(self, excel_file: str, include_read_count: bool = False) -> List[Dict]:
        """运行分析流程"""
        # 读取Excel数据
        try:
            links, institutions, dates, pre_contents = self.file_handler.read_excel_links(excel_file)

            # 读取额外信息
            read_counts, titles = self._read_extra_info(excel_file) if include_read_count else (
            [0] * len(links), [''] * len(links))

        except Exception as e:
            self.logger.error(f"读取文件失败: {e}")
            return []

        if not links:
            self.logger.error("未找到任何链接")
            return []

        self.logger.info(f"读取到 {len(links)} 个链接")

        # 分析文章
        all_analyses = []
        successful_count = 0
        failed_count = 0

        for i, (link, inst, date_str, pre_content, read_count, title) in enumerate(
                zip(links, institutions, dates, pre_contents, read_counts, titles), 1
        ):
            self.logger.info(f"\n{'=' * 60}")
            self.logger.info(f"[{i}/{len(links)}] 开始分析")
            self.logger.info(f"机构: {inst}")
            self.logger.info(f"日期: {self.data_processor.parse_date(date_str)}")
            self.logger.info(f"链接: {link}")

            if title:
                self.logger.info(f"标题: {title}")
            if read_count > 0:
                self.logger.info(f"阅读量: {read_count}")

            try:
                # 获取内容
                content = self._get_article_content(link, inst, date_str, title, pre_content)

                if not content or len(content) < 100:
                    self.logger.warning("文章内容过短或为空，跳过")
                    failed_count += 1
                    continue

                # 清理内容
                content = self.data_processor.clean_text(content)

                # 分析文章
                analysis = self.article_analyzer.analyze(content, link, inst, str(date_str))

                # AI增强评分
                self.logger.info("使用AI进行增强评分...")
                enhanced_score = self.data_processor.calculate_article_score_with_ai(
                    analysis, read_count
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
                self.logger.info("等待3秒后继续...")
                time.sleep(3)

        # 输出统计
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"文章分析完成统计:")
        self.logger.info(f"- 成功: {successful_count}")
        self.logger.info(f"- 失败: {failed_count}")
        self.logger.info(f"- 成功率: {successful_count / len(links) * 100:.1f}%")
        self.logger.info(f"{'=' * 60}")

        return all_analyses

    def _read_extra_info(self, excel_file: str) -> tuple:
        """读取额外信息（阅读数、标题）"""
        try:
            df = pd.read_excel(os.path.join('data', 'input', excel_file))

            read_counts = df['阅读数'].fillna(0).astype(int).tolist() if '阅读数' in df.columns else [0] * len(df)
            titles = df['文章标题'].fillna('').tolist() if '文章标题' in df.columns else [''] * len(df)

            return read_counts, titles
        except:
            return [], []

    def _get_article_content(self, link: str, inst: str, date_str: str,
                             title: str, pre_content: str) -> str:
        """获取文章内容"""
        # 优先使用预存内容
        if pre_content and str(pre_content) != 'nan' and len(str(pre_content)) > 100:
            self.logger.info("使用Excel中预存的文章内容")
            return str(pre_content)

        # 否则爬取内容
        return self.crawler_manager.fetch_article_content(link, inst, date_str, title)