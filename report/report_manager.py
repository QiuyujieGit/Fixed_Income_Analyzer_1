"""报告管理器 - 统一管理所有报告生成功能"""
import os
from datetime import datetime
from typing import List, Dict
import pandas as pd
from .excel_generator import ExcelGenerator
from .text_generator import TextGenerator
from analyzer.market_analyzer import MarketAnalyzer
from api.deepseek_client import DeepSeekClient
from utils.logger import setup_logger
from utils.data_processor import DataProcessor


class ReportManager:
    """报告管理器"""

    def __init__(self):
        self.logger = setup_logger("ReportManager")
        self.excel_generator = ExcelGenerator()
        self.text_generator = TextGenerator()
        self.deepseek_client = DeepSeekClient()
        self.market_analyzer = MarketAnalyzer(self.deepseek_client)
        self.data_processor = DataProcessor(deepseek_client=self.deepseek_client)

    def generate_reports(self, analyses: List[Dict]):
        """生成所有报告"""
        if not analyses:
            self.logger.error("没有可用的分析结果")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        self.logger.info(f"\n{'=' * 80}")
        self.logger.info("开始生成AI增强分析报告...")
        self.logger.info(f"{'=' * 80}")

        # AI增强分析
        self.logger.info("\n正在进行AI增强分析...")

        # 收益率预测聚合
        self.logger.info("1. AI收益率预测聚合统计...")
        yield_predictions = self.data_processor.extract_yield_predictions_with_ai(analyses)
        self.logger.info("✓ AI收益率预测聚合完成")

        # 主要观点NLP提炼
        self.logger.info("2. AI主要观点NLP提炼...")
        key_opinions = self.data_processor.extract_key_opinions_with_ai(analyses)
        self.logger.info("✓ AI主要观点提炼完成")

        # 生成统计信息
        self.logger.info("3. 生成综合统计信息...")
        metadata = self.data_processor.merge_analyses(analyses)
        self.logger.info("✓ 综合统计完成")

        # 生成Excel报告
        self._generate_excel_report(analyses, yield_predictions, key_opinions, metadata, timestamp)

        # 生成文本报告
        self._generate_text_report(analyses, yield_predictions, key_opinions, metadata, timestamp)

    def _generate_excel_report(self, analyses, yield_predictions, key_opinions, metadata, timestamp):
        """生成Excel报告"""
        self.logger.info("\n生成Excel报告...")

        try:
            # 使用增强的Excel生成器
            excel_path = self.excel_generator.generate_enhanced_report(
                analyses, yield_predictions, key_opinions, metadata, timestamp
            )

            if excel_path:
                self.logger.info(f"✓ 增强Excel报告已生成: {excel_path}")
            else:
                self.logger.error("✗ Excel报告生成失败")

        except Exception as e:
            self.logger.error(f"✗ 生成增强Excel失败: {e}")
            import traceback
            traceback.print_exc()

    def _generate_text_report(self, analyses, yield_predictions, key_opinions, metadata, timestamp):
        """生成文本报告"""
        self.logger.info("\n生成综合文本报告...")

        try:
            # 使用AI生成综合分析
            summary = self.market_analyzer.generate_summary(analyses)

            # 添加增强内容
            enhanced_summary = self._enhance_summary_with_ai_insights(
                summary, yield_predictions, key_opinions, metadata
            )

            # 生成文本报告
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

    def _enhance_summary_with_ai_insights(self, summary: str, yield_predictions: dict,
                                          key_opinions: dict, metadata: dict) -> str:
        """使用AI洞察增强总结报告"""
        enhanced_parts = [summary]

        # 添加AI增强分析洞察
        enhanced_parts.extend([
            "\n" + "=" * 80,
            "【AI增强分析洞察】",
            "=" * 80
        ])

        # 1. 收益率预测统计
        enhanced_parts.extend(self._format_yield_predictions(yield_predictions))

        # 2. 主要观点提炼
        enhanced_parts.extend(self._format_key_opinions(key_opinions))

        # 3. 评分分布分析
        enhanced_parts.extend(self._format_score_distribution(metadata))

        # 4. 市场关注度分析
        enhanced_parts.extend(self._format_market_attention(metadata))

        # 5. 关键词云分析
        enhanced_parts.extend(self._format_keyword_cloud(metadata))

        # 添加生成时间
        enhanced_parts.extend([
            "\n" + "=" * 80,
            f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80
        ])

        return '\n'.join(enhanced_parts)

    def _format_yield_predictions(self, yield_predictions):
        """格式化收益率预测"""
        parts = [
            "\n一、AI收益率预测聚合分析",
            "-" * 40
        ]

        if '10Y' in yield_predictions and isinstance(yield_predictions['10Y'], dict):
            for term in ['10Y', '5Y']:
                if term in yield_predictions:
                    pred = yield_predictions[term]
                    max_direction, max_count = self._find_max_direction(pred)
                    if max_direction:
                        parts.append(
                            f"{term}国债：{max_direction}为主流观点（{max_count}家机构，"
                            f"占比{pred[max_direction].get('percentage', 0)}%），"
                            f"平均评分{pred[max_direction].get('avg_score', 0)}"
                        )
        elif 'market_consensus' in yield_predictions:
            parts.append(yield_predictions.get('summary', '暂无预测数据'))

        return parts

    def _find_max_direction(self, predictions):
        """找出主流观点"""
        max_direction = None
        max_count = 0
        for direction in ['上行', '下行', '震荡']:
            if direction in predictions and predictions[direction].get('count', 0) > max_count:
                max_count = predictions[direction]['count']
                max_direction = direction
        return max_direction, max_count

    def _format_key_opinions(self, key_opinions):
        """格式化主要观点"""
        parts = [
            "\n\n二、AI主要观点NLP提炼",
            "-" * 40
        ]

        if isinstance(key_opinions, dict):
            priority_categories = ['利率走势核心观点', '政策预期核心观点', '投资策略核心观点', '市场情绪核心观点']

            for category in priority_categories:
                if category in key_opinions:
                    content = key_opinions[category]
                    parts.append(f"\n{category}：")
                    if isinstance(content, str):
                        parts.append(f"{content[:200]}..." if len(content) > 200 else content)
                    elif isinstance(content, list) and content:
                        parts.append(f"- {content[0][:150]}..." if len(content[0]) > 150 else f"- {content[0]}")

        return parts

    def _format_score_distribution(self, metadata):
        """格式化评分分布"""
        parts = [
            "\n\n三、文章质量评分分布",
            "-" * 40
        ]

        if 'score_distribution' in metadata:
            dist = metadata['score_distribution']
            total = sum(dist.values())
            if total > 0:
                for score_range, count in sorted(dist.items(), reverse=True):
                    percentage = count / total * 100
                    parts.append(f"{score_range}：{count}篇（{percentage:.1f}%）")

        return parts

    def _format_market_attention(self, metadata):
        """格式化市场关注度"""
        parts = [
            "\n\n四、市场关注度分析",
            "-" * 40
        ]

        if 'read_count_stats' in metadata:
            stats = metadata['read_count_stats']
            if stats.get('total', 0) > 0:
                parts.extend([
                    f"总阅读量：{stats.get('total', 0):,}",
                    f"平均阅读量：{int(stats.get('average', 0)):,}",
                    f"高关注度文章（阅读量>5000）：{stats.get('high_impact_count', 0)}篇"
                ])

                if stats.get('high_impact_count', 0) > 0:
                    parts.append("\n说明：高阅读量文章通常反映市场关注热点，已纳入评分权重考虑")

        return parts

    def _format_keyword_cloud(self, metadata):
        """格式化关键词云"""
        parts = []

        if 'opinion_cloud' in metadata and metadata['opinion_cloud']:
            parts.extend([
                "\n\n五、高频关键词（前10）",
                "-" * 40
            ])

            top_words = sorted(metadata['opinion_cloud'].items(), key=lambda x: x[1], reverse=True)[:10]
            keywords = [f"{word}({count})" for word, count in top_words]
            parts.append("、".join(keywords))

        return parts