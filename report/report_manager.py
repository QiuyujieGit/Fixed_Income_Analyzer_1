"""报告管理器 - 统一管理所有报告生成功能"""
import os
import json
from datetime import datetime
from typing import List, Dict
import pandas as pd
from .excel_generator import ExcelGenerator
from .text_generator import TextGenerator
from api.deepseek_client import DeepSeekClient
from utils.logger import setup_logger
from utils.data_processor import DataProcessor
from analyzer.prompt import SUMMARY_REPORT_PROMPT
from config.setting import OUTPUT_DIR, ANALYSIS_DIMENSIONS


class ReportManager:
    """报告管理器"""

    def __init__(self):
        self.logger = setup_logger("ReportManager")
        self.output_dir = OUTPUT_DIR  # 添加output_dir属性
        self.analysis_dimensions = ANALYSIS_DIMENSIONS  # 添加分析维度
        self.excel_generator = ExcelGenerator()
        self.text_generator = TextGenerator()
        self.deepseek_client = DeepSeekClient()
        self.data_processor = DataProcessor(deepseek_client=self.deepseek_client)

    def generate_reports(self, analyses: List[Dict]):
        """生成所有报告 - 简化版"""
        if not analyses:
            self.logger.error("没有可用的分析结果")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        self.logger.info(f"\n{'=' * 80}")
        self.logger.info("开始生成分析报告...")
        self.logger.info(f"{'=' * 80}")

        # 生成Excel报告
        self._generate_excel_report(analyses, timestamp)

        # 生成文本报告
        self._generate_text_report(analyses, timestamp)

    def _generate_excel_report(self, analyses, timestamp):
        """生成Excel报告"""
        self.logger.info("\n生成Excel报告...")

        try:
            # 直接调用excel_generator的方法
            excel_path = self.excel_generator.generate_report(analyses, timestamp)

            if excel_path:
                self.logger.info(f"✓ Excel报告已生成: {excel_path}")
            else:
                self.logger.error("✗ Excel报告生成失败")

        except Exception as e:
            self.logger.error(f"✗ 生成Excel失败: {e}")
            import traceback
            traceback.print_exc()

    def _generate_text_report(self, analyses, timestamp):
        """生成文本报告 - 新格式"""
        self.logger.info("\n生成市场观点内参...")

        try:
            # 统计态度
            attitude_stats = self._calculate_attitude_statistics(analyses)

            # 整理各维度观点
            dimension_views = self._extract_dimension_views(analyses)

            # 构建提示词
            prompt = SUMMARY_REPORT_PROMPT.format(
                total_count=len(analyses),
                bullish_10y=attitude_stats['10Y']['看多'],
                bearish_10y=attitude_stats['10Y']['看空'],
                neutral_10y=attitude_stats['10Y']['中性'],
                bullish_5y=attitude_stats['5Y']['看多'],
                bearish_5y=attitude_stats['5Y']['看空'],
                neutral_5y=attitude_stats['5Y']['中性'],
                fundamental_views=json.dumps(dimension_views['基本面及通胀'], ensure_ascii=False),
                liquidity_views=json.dumps(dimension_views['资金面'], ensure_ascii=False),
                policy_views=json.dumps(dimension_views['货币及财政政策'], ensure_ascii=False),
                institutional_views=json.dumps(dimension_views['机构行为'], ensure_ascii=False),
                overseas_views=json.dumps(dimension_views['海外及其他'], ensure_ascii=False)
            )

            # 生成报告
            summary = self.deepseek_client.chat(prompt)

            # 保存报告
            report_path = os.path.join(
                self.output_dir,
                f'债券市场观点内参_{timestamp}.txt'
            )

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"债券市场观点内参\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"分析文章数: {len(analyses)}篇\n")
                f.write("=" * 80 + "\n\n")
                f.write(summary)

            self.logger.info(f"✓ 观点内参已生成: {report_path}")

            # 在控制台显示
            print("\n" + "=" * 80)
            print("【债券市场观点内参】")
            print("=" * 80)
            print(summary)
            print("=" * 80)

        except Exception as e:
            self.logger.error(f"✗ 生成文本报告失败: {e}")
            import traceback
            traceback.print_exc()

    def _generate_text_report(self, analyses, timestamp):
        """生成文本报告 - 新格式"""
        self.logger.info("\n生成市场观点内参...")

        try:
            # 统计态度
            attitude_stats = self._calculate_attitude_statistics(analyses)

            # 整理各维度观点
            dimension_views = self._extract_dimension_views(analyses)

            # 构建提示词
            prompt = SUMMARY_REPORT_PROMPT.format(
                total_count=len(analyses),
                bullish_10y=attitude_stats['10Y']['看多'],
                bearish_10y=attitude_stats['10Y']['看空'],
                neutral_10y=attitude_stats['10Y']['中性'],
                bullish_5y=attitude_stats['5Y']['看多'],
                bearish_5y=attitude_stats['5Y']['看空'],
                neutral_5y=attitude_stats['5Y']['中性'],
                fundamental_views=json.dumps(dimension_views['基本面及通胀'], ensure_ascii=False),
                liquidity_views=json.dumps(dimension_views['资金面'], ensure_ascii=False),
                policy_views=json.dumps(dimension_views['货币及财政政策'], ensure_ascii=False),
                institutional_views=json.dumps(dimension_views['机构行为'], ensure_ascii=False),
                overseas_views=json.dumps(dimension_views['海外及其他'], ensure_ascii=False)
            )

            # 生成报告
            summary = self.deepseek_client.chat(prompt)

            # 保存报告
            report_path = os.path.join(
                self.output_dir,
                f'债券市场观点内参_{timestamp}.txt'
            )

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"债券市场观点内参\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"分析文章数: {len(analyses)}篇\n")
                f.write("=" * 80 + "\n\n")
                f.write(summary)

            self.logger.info(f"✓ 观点内参已生成: {report_path}")

            # 在控制台显示
            print("\n" + "=" * 80)
            print("【债券市场观点内参】")
            print("=" * 80)
            print(summary)
            print("=" * 80)

        except Exception as e:
            self.logger.error(f"✗ 生成文本报告失败: {e}")
            import traceback
            traceback.print_exc()

    def _calculate_attitude_statistics(self, analyses):
        """统计态度分布"""
        stats = {
            '10Y': {'看多': 0, '看空': 0, '中性': 0, '未涉及': 0},
            '5Y': {'看多': 0, '看空': 0, '中性': 0, '未涉及': 0}
        }

        for analysis in analyses:
            # 10Y态度
            attitude_10y = analysis.get('10Y国债态度', '文章未涉及')
            if '多' in attitude_10y:
                stats['10Y']['看多'] += 1
            elif '空' in attitude_10y:
                stats['10Y']['看空'] += 1
            elif '中性' in attitude_10y or '震荡' in attitude_10y:
                stats['10Y']['中性'] += 1
            else:
                stats['10Y']['未涉及'] += 1

            # 5Y态度
            attitude_5y = analysis.get('5Y国债态度', '文章未涉及')
            if '多' in attitude_5y:
                stats['5Y']['看多'] += 1
            elif '空' in attitude_5y:
                stats['5Y']['看空'] += 1
            elif '中性' in attitude_5y or '震荡' in attitude_5y:
                stats['5Y']['中性'] += 1
            else:
                stats['5Y']['未涉及'] += 1

        return stats

    def _extract_dimension_views(self, analyses):
        """提取各维度观点"""
        views = {dim: [] for dim in self.analysis_dimensions}

        for analysis in analyses:
            institution = analysis.get('机构', '')
            for dim in self.analysis_dimensions:
                content = analysis.get(dim, '')
                if content and len(content) > 20:
                    views[dim].append(f"{institution}: {content}")

        # 每个维度最多保留5条
        for dim in views:
            views[dim] = views[dim][:5]

        return views
