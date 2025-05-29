"""主程序入口 - 完整版本"""
import sys
import os
import hashlib
import time
import json
import logging
from datetime import datetime, date
import pandas as pd
import numpy as np

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
    """债券市场分析系统 - AI增强版"""

    def __init__(self):
        self.logger = setup_logger("BondAnalyzer")
        self.logger.info("=" * 80)
        self.logger.info("初始化债券市场分析系统 - AI增强版")
        self.logger.info("=" * 80)

        try:
            # 初始化核心组件
            self.deepseek_client = DeepSeekClient()
            self.logger.info("✓ DeepSeek客户端初始化成功")

            # 初始化爬虫组件
            self.wechat_crawler = WechatCrawler()
            self.batch_crawler = WechatBatchCrawler()
            self.jina_crawler = JinaCrawler()
            self.logger.info("✓ 爬虫组件初始化成功")

            # 初始化分析器
            self.article_analyzer = ArticleAnalyzer(self.deepseek_client)
            self.market_analyzer = MarketAnalyzer(self.deepseek_client)
            self.logger.info("✓ 分析器初始化成功")

            # 初始化工具类 - 使用AI增强的数据处理器
            self.file_handler = FileHandler()
            self.data_processor = DataProcessor(deepseek_client=self.deepseek_client)
            self.logger.info("✓ AI增强数据处理器初始化成功")

            # 初始化报告生成器
            self.excel_generator = ExcelGenerator()
            self.text_generator = TextGenerator()
            self.logger.info("✓ 报告生成器初始化成功")

            # 初始化去重系统
            self.hash_cache_file = os.path.join('data', 'cache', 'article_hashes.json')
            self.article_hashes = self._load_article_hashes()
            self.logger.info("✓ 去重系统初始化成功")

            self.logger.info("=" * 80)
            self.logger.info("所有组件初始化成功！")
            self.logger.info("=" * 80)

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
        print("债券市场观点自动化分析系统 - AI增强版")
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
                days = int(input("请输入天数 (默认7天): ") or "7")
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

            # 确保目录存在
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)

            df = pd.DataFrame(excel_data)
            df.to_excel(temp_path, index=False)

            self.logger.info(f"创建临时分析文件: {temp_filename}")

            # 运行分析
            self._run_analysis(temp_filename, include_read_count=True)

            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
                self.logger.info("临时文件已清理")

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

    def _run_analysis(self, excel_file: str, include_read_count: bool = False):
        """运行分析流程（共用部分）- AI增强版"""
        # 读取链接
        try:
            links, institutions, dates, pre_contents = self.file_handler.read_excel_links(excel_file)

            # 如果包含阅读数，尝试读取
            read_counts = []
            if include_read_count:
                try:
                    df = pd.read_excel(os.path.join('data', 'input', excel_file))
                    if '阅读数' in df.columns:
                        read_counts = df['阅读数'].fillna(0).astype(int).tolist()
                    else:
                        read_counts = [0] * len(links)
                except:
                    read_counts = [0] * len(links)
            else:
                read_counts = [0] * len(links)

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

        for i, (link, inst, date_str, pre_content, read_count) in enumerate(
            zip(links, institutions, dates, pre_contents, read_counts), 1
        ):
            self.logger.info(f"\n{'=' * 60}")
            self.logger.info(f"[{i}/{len(links)}] 开始分析")
            self.logger.info(f"机构: {inst}")
            self.logger.info(f"日期: {self.data_processor.parse_date(date_str)}")
            self.logger.info(f"链接: {link}")
            if read_count > 0:
                self.logger.info(f"阅读量: {read_count}")

            try:
                # 获取内容
                if pre_content and str(pre_content) != 'nan' and len(str(pre_content)) > 100:
                    self.logger.info("使用Excel中预存的文章内容")
                    content = str(pre_content)
                else:
                    content = self._fetch_article_content(link, inst, date_str)

                if not content or len(content) < 100:
                    self.logger.warning("文章内容过短或为空，跳过")
                    failed_count += 1
                    continue

                # 清理内容
                content = self.data_processor.clean_text(content)

                # 分析文章
                analysis = self.article_analyzer.analyze(content, link, inst, str(date_str))

                # 使用AI增强评分（TODO 3.2 & 3.3）
                self.logger.info("使用AI进行增强评分...")
                enhanced_score = self.data_processor.calculate_article_score_with_ai(
                    analysis,
                    read_count
                )
                analysis.update(enhanced_score)

                # 验证分析结果
                if self.data_processor.validate_analysis_result(analysis):
                    all_analyses.append(analysis)
                    successful_count += 1
                    self.logger.info(f"分析完成 - 评分: {analysis.get('重要性评分')} (阅读量影响: {read_count})")
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

        # 生成增强报告
        if all_analyses:
            self._generate_enhanced_reports(all_analyses)
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

    def _generate_enhanced_reports(self, analyses: list):
        """生成增强报告 - AI增强版"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        self.logger.info(f"\n{'=' * 80}")
        self.logger.info("开始生成AI增强分析报告...")
        self.logger.info(f"{'=' * 80}")

        # 使用AI增强功能生成统计
        self.logger.info("\n正在进行AI增强分析...")

        # TODO 3.1: 收益率预测聚合
        self.logger.info("1. AI收益率预测聚合统计...")
        yield_predictions = self.data_processor.extract_yield_predictions_with_ai(analyses)
        self.logger.info("✓ AI收益率预测聚合完成")

        # TODO 3.4: 主要观点NLP提炼
        self.logger.info("2. AI主要观点NLP提炼...")
        key_opinions = self.data_processor.extract_key_opinions_with_ai(analyses)
        self.logger.info("✓ AI主要观点提炼完成")

        # 生成完整统计信息
        self.logger.info("3. 生成综合统计信息...")
        metadata = self.data_processor.merge_analyses(analyses)
        self.logger.info("✓ 综合统计完成")

        # 生成增强的Excel报告
        self.logger.info("\n生成Excel报告...")
        try:
            excel_path = os.path.join('data', 'output', f'债券市场分析结果_AI增强_{timestamp}.xlsx')

            # 确保输出目录存在
            os.makedirs(os.path.dirname(excel_path), exist_ok=True)

            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # 1. 主要分析结果
                summary_df = self.excel_generator.create_summary_dataframe(analyses)
                summary_df.to_excel(writer, sheet_name='分析结果', index=False)
                self.logger.info("  ✓ 分析结果sheet完成")

                # 2. 收益率预测统计（TODO 3.1）
                yield_df = self._create_yield_prediction_dataframe(yield_predictions)
                yield_df.to_excel(writer, sheet_name='收益率预测统计', index=False)
                self.logger.info("  ✓ 收益率预测统计sheet完成")

                # 3. 评分分布统计（TODO 3.3）
                score_df = self._create_score_distribution_dataframe(metadata.get('score_distribution', {}))
                score_df.to_excel(writer, sheet_name='评分分布', index=False)
                self.logger.info("  ✓ 评分分布sheet完成")

                # 4. 主要观点汇总（TODO 3.4）
                opinions_df = self._create_key_opinions_dataframe(key_opinions)
                opinions_df.to_excel(writer, sheet_name='主要观点', index=False)
                self.logger.info("  ✓ 主要观点sheet完成")

                # 5. 阅读量统计（TODO 3.2）
                read_stats_df = self._create_read_count_stats_dataframe(metadata.get('read_count_stats', {}))
                read_stats_df.to_excel(writer, sheet_name='阅读量统计', index=False)
                self.logger.info("  ✓ 阅读量统计sheet完成")

                # 6. 机构统计
                institution_df = self._create_institution_stats_dataframe(analyses)
                institution_df.to_excel(writer, sheet_name='机构统计', index=False)
                self.logger.info("  ✓ 机构统计sheet完成")

            self.logger.info(f"\n✓ 增强Excel报告已生成: {excel_path}")

        except Exception as e:
            self.logger.error(f"✗ 生成增强Excel失败: {e}")
            import traceback
            traceback.print_exc()

        # 生成文本报告
        self.logger.info("\n生成综合文本报告...")
        try:
            # 使用AI生成综合分析
            summary = self.market_analyzer.generate_summary(analyses)

            # 添加增强内容
            enhanced_summary = self._enhance_summary_with_ai_insights(
                summary, yield_predictions, key_opinions, metadata
            )

            text_path = self.text_generator.generate(enhanced_summary, timestamp, metadata)
            self.logger.info(f"✓ 增强文本报告已生成: {text_path}")

            # 在控制台显示报告
            print("\n" + "=" * 80)
            print("【债券市场观点总结报告 - AI增强版】")
            print("=" * 80)
            print(enhanced_summary)
            print("=" * 80)

        except Exception as e:
            self.logger.error(f"✗ 生成增强文本报告失败: {e}")
            import traceback
            traceback.print_exc()

    def _create_yield_prediction_dataframe(self, predictions: dict) -> pd.DataFrame:
        """创建收益率预测统计DataFrame"""
        data = []

        # 如果predictions是基础格式
        if '10Y' in predictions and isinstance(predictions['10Y'], dict):
            for term in ['10Y', '5Y']:
                if term in predictions:
                    for direction in ['上行', '下行', '震荡', '未涉及']:
                        if direction in predictions[term]:
                            stats = predictions[term][direction]
                            data.append({
                                '期限': term,
                                '预测方向': direction,
                                '机构数量': stats.get('count', 0),
                                '占比': f"{stats.get('percentage', 0)}%",
                                '平均评分': stats.get('avg_score', 0),
                                '主要机构': ', '.join(stats.get('institutions', [])[:5])
                            })

        # 如果predictions是AI增强格式
        elif 'total_institutions' in predictions:
            # 添加总体统计
            data.append({
                '期限': '总体',
                '预测方向': '统计',
                '机构数量': predictions.get('total_institutions', 0),
                '占比': '100%',
                '平均评分': '-',
                '主要机构': f"分析日期: {predictions.get('analysis_date', '')}"
            })

            # 添加其他AI生成的统计信息
            if '10Y预测统计' in predictions:
                for direction, stats in predictions['10Y预测统计'].items():
                    data.append({
                        '期限': '10Y',
                        '预测方向': direction,
                        '机构数量': stats.get('数量', 0),
                        '占比': stats.get('占比', '0%'),
                        '平均评分': '-',
                        '主要机构': ', '.join(stats.get('主要机构', [])[:3])
                    })

        if not data:
            # 返回空DataFrame
            data = [{
                '期限': '-',
                '预测方向': '-',
                '机构数量': 0,
                '占比': '0%',
                '平均评分': 0,
                '主要机构': '-'
            }]

        return pd.DataFrame(data)

    def _create_score_distribution_dataframe(self, distribution: dict) -> pd.DataFrame:
        """创建评分分布DataFrame"""
        data = []

        if distribution:
            total = sum(distribution.values())
            for score_range, count in distribution.items():
                data.append({
                    '评分区间': score_range,
                    '文章数量': count,
                    '占比': f"{count / total * 100:.1f}%" if total > 0 else "0%",
                    '评分说明': self._get_score_range_description(score_range)
                })
        else:
            # 默认数据
            data = [{
                '评分区间': '-',
                '文章数量': 0,
                '占比': '0%',
                '评分说明': '-'
            }]

        return pd.DataFrame(data)

    def _get_score_range_description(self, score_range: str) -> str:
        """获取评分区间说明"""
        descriptions = {
            '9-10分': '极具价值，观点独特，数据翔实',
            '7-8分': '有价值，观点清晰，有数据支撑',
            '5-6分': '一般价值，观点常规，数据一般',
            '3-4分': '价值较低，观点模糊，缺乏数据',
            '1-2分': '几乎无价值'
        }
        return descriptions.get(score_range, '')

    def _create_key_opinions_dataframe(self, opinions: dict) -> pd.DataFrame:
        """创建主要观点DataFrame"""
        data = []

        if isinstance(opinions, dict):
            # 处理不同格式的观点数据
            for category, content in opinions.items():
                if isinstance(content, list):
                    for i, item in enumerate(content, 1):
                        data.append({
                            '观点类别': category,
                            '序号': i,
                            '具体内容': str(item)[:200] + '...' if len(str(item)) > 200 else str(item)
                        })
                elif isinstance(content, dict):
                    # 处理嵌套字典
                    for sub_key, sub_content in content.items():
                        data.append({
                            '观点类别': f"{category}-{sub_key}",
                            '序号': 1,
                            '具体内容': str(sub_content)[:200] + '...' if len(str(sub_content)) > 200 else str(sub_content)
                        })
                else:
                    data.append({
                        '观点类别': category,
                        '序号': 1,
                        '具体内容': str(content)[:200] + '...' if len(str(content)) > 200 else str(content)
                    })

        if not data:
            data = [{
                '观点类别': '-',
                '序号': 0,
                '具体内容': '暂无观点数据'
            }]

        return pd.DataFrame(data)

    def _create_read_count_stats_dataframe(self, stats: dict) -> pd.DataFrame:
        """创建阅读量统计DataFrame"""
        data = []

        if stats and stats.get('total', 0) > 0:
            data = [
                {'统计项': '总阅读量', '数值': f"{stats.get('total', 0):,}"},
                {'统计项': '平均阅读量', '数值': f"{int(stats.get('average', 0)):,}"},
                {'统计项': '最高阅读量', '数值': f"{stats.get('max', 0):,}"},
                {'统计项': '最低阅读量', '数值': f"{stats.get('min', 0):,}"},
                {'统计项': '高关注度文章数', '数值': f"{stats.get('high_impact_count', 0)} 篇 (阅读量>5000)"},
            ]
        else:
            data = [{'统计项': '暂无数据', '数值': '-'}]

        return pd.DataFrame(data)

    def _create_institution_stats_dataframe(self, analyses: list[dict]) -> pd.DataFrame:
        """创建机构统计DataFrame"""
        institution_stats = {}

        for analysis in analyses:
            inst = analysis.get('机构', '未知')
            if inst not in institution_stats:
                institution_stats[inst] = {
                    '文章数': 0,
                    '总评分': 0,
                    '总阅读量': 0,
                    '最高评分': 0,
                    '最低评分': 10
                }

            stats = institution_stats[inst]
            stats['文章数'] += 1
            score = analysis.get('重要性评分', 0)
            stats['总评分'] += score
            stats['总阅读量'] += analysis.get('阅读量', 0)
            stats['最高评分'] = max(stats['最高评分'], score)
            stats['最低评分'] = min(stats['最低评分'], score)

        # 转换为DataFrame格式
        data = []
        for inst, stats in institution_stats.items():
            data.append({
                '机构名称': inst,
                '发布文章数': stats['文章数'],
                '平均评分': round(stats['总评分'] / stats['文章数'], 2) if stats['文章数'] > 0 else 0,
                '最高评分': stats['最高评分'],
                '最低评分': stats['最低评分'] if stats['最低评分'] < 10 else 0,
                '总阅读量': f"{stats['总阅读量']:,}",
                '平均阅读量': f"{stats['总阅读量'] // stats['文章数']:,}" if stats['文章数'] > 0 else "0"
            })

        # 按平均评分排序
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values('平均评分', ascending=False)

        return df

    def _enhance_summary_with_ai_insights(self, summary: str, yield_predictions: dict,
                                        key_opinions: dict, metadata: dict) -> str:
        """使用AI洞察增强总结报告"""
        enhanced_parts = [summary]

        # 添加分隔线
        enhanced_parts.append("\n" + "=" * 80)
        enhanced_parts.append("【AI增强分析洞察】")
        enhanced_parts.append("=" * 80)

        # 1. 添加收益率预测统计（TODO 3.1）
        enhanced_parts.append("\n一、AI收益率预测聚合分析")
        enhanced_parts.append("-" * 40)

        if '10Y' in yield_predictions and isinstance(yield_predictions['10Y'], dict):
            # 基础格式
            for term in ['10Y', '5Y']:
                if term in yield_predictions:
                    pred = yield_predictions[term]
                    # 找出主流观点
                    max_direction = None
                    max_count = 0
                    for direction in ['上行', '下行', '震荡']:
                        if direction in pred and pred[direction].get('count', 0) > max_count:
                            max_count = pred[direction]['count']
                            max_direction = direction

                    if max_direction:
                        enhanced_parts.append(
                            f"{term}国债：{max_direction}为主流观点（{pred[max_direction]['count']}家机构，"
                            f"占比{pred[max_direction].get('percentage', 0)}%），"
                            f"平均评分{pred[max_direction].get('avg_score', 0)}"
                        )
        elif 'market_consensus' in yield_predictions:
            # AI增强格式
            enhanced_parts.append(yield_predictions.get('summary', '暂无预测数据'))

        # 2. 添加主要观点提炼（TODO 3.4）
        enhanced_parts.append("\n\n二、AI主要观点NLP提炼")
        enhanced_parts.append("-" * 40)

        if isinstance(key_opinions, dict):
            # 优先显示的观点类别
            priority_categories = ['利率走势核心观点', '政策预期核心观点', '投资策略核心观点', '市场情绪核心观点']

            for category in priority_categories:
                if category in key_opinions:
                    content = key_opinions[category]
                    if isinstance(content, str):
                        enhanced_parts.append(f"\n{category}：")
                        enhanced_parts.append(f"{content[:200]}..." if len(content) > 200 else content)
                    elif isinstance(content, list) and content:
                        enhanced_parts.append(f"\n{category}：")
                        enhanced_parts.append(f"- {content[0][:150]}..." if len(content[0]) > 150 else f"- {content[0]}")

        # 3. 添加评分分布分析（TODO 3.3）
        enhanced_parts.append("\n\n三、文章质量评分分布")
        enhanced_parts.append("-" * 40)

        if 'score_distribution' in metadata:
            dist = metadata['score_distribution']
            total = sum(dist.values())
            if total > 0:
                for score_range, count in sorted(dist.items(), reverse=True):
                    percentage = count / total * 100
                    enhanced_parts.append(f"{score_range}：{count}篇（{percentage:.1f}%）")

        # 4. 添加阅读量影响分析（TODO 3.2）
        enhanced_parts.append("\n\n四、市场关注度分析")
        enhanced_parts.append("-" * 40)

        if 'read_count_stats' in metadata:
            stats = metadata['read_count_stats']
            if stats.get('total', 0) > 0:
                enhanced_parts.append(f"总阅读量：{stats.get('total', 0):,}")
                enhanced_parts.append(f"平均阅读量：{int(stats.get('average', 0)):,}")
                enhanced_parts.append(f"高关注度文章（阅读量>5000）：{stats.get('high_impact_count', 0)}篇")

                # 计算关注度与评分的关系
                if stats.get('high_impact_count', 0) > 0:
                    enhanced_parts.append("\n说明：高阅读量文章通常反映市场关注热点，已纳入评分权重考虑")

        # 5. 添加关键词云分析
        if 'opinion_cloud' in metadata and metadata['opinion_cloud']:
            enhanced_parts.append("\n\n五、高频关键词（前10）")
            enhanced_parts.append("-" * 40)

            top_words = sorted(metadata['opinion_cloud'].items(), key=lambda x: x[1], reverse=True)[:10]
            keywords = [f"{word}({count})" for word, count in top_words]
            enhanced_parts.append("、".join(keywords))

        # 添加生成时间
        enhanced_parts.append("\n" + "=" * 80)
        enhanced_parts.append(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        enhanced_parts.append("=" * 80)

        return '\n'.join(enhanced_parts)


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
                if len(sys.argv) > 2:
                    # 直接运行Excel模式
                    system._run_analysis(sys.argv[2])
                else:
                    system.run(mode='excel')
            elif sys.argv[1] == '--help':
                print("\n使用方法:")
                print("  python Main.py              # 交互式选择模式")
                print("  python Main.py --crawl      # 爬取公众号模式")
                print("  python Main.py --excel      # Excel链接模式")
                print("  python Main.py --excel filename.xlsx  # 直接分析指定Excel文件")
            else:
                print(f"未知参数: {sys.argv[1]}")
                print("使用 --help 查看帮助")
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
