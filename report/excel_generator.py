"""Excel报告生成器 - 增强版"""
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from config.setting import OUTPUT_DIR
from utils.logger import setup_logger


class ExcelGenerator:
    """Excel报告生成器"""

    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.logger = setup_logger("ExcelGenerator")

    def generate_enhanced_report(self, analyses: List[Dict[str, Any]],
                                 yield_predictions: dict, key_opinions: dict,
                                 metadata: dict, timestamp: str) -> str:
        """生成增强版Excel报告"""
        try:
            excel_path = os.path.join(self.output_dir, f'债券市场分析结果_AI增强_{timestamp}.xlsx')
            os.makedirs(os.path.dirname(excel_path), exist_ok=True)

            # 准备所有的DataFrame
            dataframes = {}

            # 1. 主要分析结果
            dataframes['分析结果'] = self.create_summary_dataframe(analyses)

            # 2. 收益率预测统计
            dataframes['收益率预测统计'] = self._create_yield_prediction_dataframe(yield_predictions)

            # 3. 评分分布统计
            dataframes['评分分布'] = self._create_score_distribution_dataframe(
                metadata.get('score_distribution', {})
            )

            # 4. 主要观点汇总
            dataframes['主要观点'] = self._create_key_opinions_dataframe(key_opinions)

            # 5. 阅读量统计
            dataframes['阅读量统计'] = self._create_read_count_stats_dataframe(
                metadata.get('read_count_stats', {})
            )

            # 6. 机构统计
            dataframes['机构统计'] = self._create_institution_stats_dataframe(analyses)

            # 写入Excel文件
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                for sheet_name, df in dataframes.items():
                    if df is not None and not df.empty:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        self._format_worksheet(writer.sheets[sheet_name], df)

            return excel_path

        except Exception as e:
            self.logger.error(f"生成Excel报告失败: {e}")
            return ""

    def create_summary_dataframe(self, analyses: List[Dict[str, Any]]) -> pd.DataFrame:
        """创建分析汇总DataFrame"""
        if not analyses:
            return pd.DataFrame()

        table_data = []
        for i, analysis in enumerate(analyses, 1):
            row = self._extract_analysis_row(i, analysis)
            table_data.append(row)

        df = pd.DataFrame(table_data)

        # 按重要性评分排序
        if not df.empty and '重要性评分' in df.columns:
            df = df.sort_values('重要性评分', ascending=False).reset_index(drop=True)
            df['序号'] = range(1, len(df) + 1)

        return df

    def _extract_analysis_row(self, index: int, analysis: Dict) -> Dict:
        """提取分析结果行数据"""
        forecast_10y = analysis.get('10Y国债收益率预测', {})
        forecast_5y = analysis.get('5Y国债收益率预测', {})
        score_details = analysis.get('评分细项', {})

        # 确保是字典类型
        forecast_10y = forecast_10y if isinstance(forecast_10y, dict) else {}
        forecast_5y = forecast_5y if isinstance(forecast_5y, dict) else {}
        score_details = score_details if isinstance(score_details, dict) else {}

        return {
            '序号': index,
            '机构': analysis.get('机构', ''),
            '发布日期': analysis.get('日期', ''),
            '文章链接': analysis.get('url', ''),
            '文章类型': ', '.join(analysis.get('文章类型', [])) if isinstance(analysis.get('文章类型'), list) else '',
            '基本面及通胀': str(analysis.get('基本面及通胀', ''))[:500],
            '资金面': str(analysis.get('资金面', ''))[:500],
            '货币及财政政策': str(analysis.get('货币及财政政策', ''))[:500],
            '机构行为': str(analysis.get('机构行为', ''))[:500],
            '海外及其他': str(analysis.get('海外及其他', ''))[:500],
            '整体观点': str(analysis.get('整体观点', ''))[:500],
            '投资策略': str(analysis.get('投资策略', ''))[:500],
            '10Y收益率预测方向': forecast_10y.get('方向', ''),
            '10Y收益率预测区间': forecast_10y.get('区间', ''),
            '10Y预测概率': forecast_10y.get('概率', ''),
            '5Y收益率预测方向': forecast_5y.get('方向', ''),
            '5Y收益率预测区间': forecast_5y.get('区间', ''),
            '5Y预测概率': forecast_5y.get('概率', ''),
            '重要性评分': analysis.get('重要性评分', 0),
            '数据支撑分': score_details.get('数据支撑', 0),
            '逻辑完整分': score_details.get('逻辑完整', 0),
            '策略价值分': score_details.get('策略价值', 0),
            '观点独特分': score_details.get('观点独特', 0),
            '市场影响分': score_details.get('市场影响', 0),
            '评分理由': str(analysis.get('评分理由', ''))[:200],
            '阅读量': analysis.get('阅读量', 0)
        }

    def _create_yield_prediction_dataframe(self, predictions: dict) -> pd.DataFrame:
        """创建收益率预测统计DataFrame"""
        data = []

        if '10Y' in predictions and isinstance(predictions['10Y'], dict):
            # 基础格式处理
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

        return pd.DataFrame(data) if data else pd.DataFrame()

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

        return pd.DataFrame(data) if data else pd.DataFrame()

    def _create_key_opinions_dataframe(self, opinions: dict) -> pd.DataFrame:
        """创建主要观点DataFrame"""
        data = []

        if isinstance(opinions, dict):
            for category, content in opinions.items():
                if isinstance(content, list):
                    for i, item in enumerate(content, 1):
                        data.append({
                            '观点类别': category,
                            '序号': i,
                            '具体内容': str(item)[:200] + '...' if len(str(item)) > 200 else str(item)
                        })
                else:
                    data.append({
                        '观点类别': category,
                        '序号': 1,
                        '具体内容': str(content)[:200] + '...' if len(str(content)) > 200 else str(content)
                    })

        return pd.DataFrame(data) if data else pd.DataFrame()

    def _create_read_count_stats_dataframe(self, stats: dict) -> pd.DataFrame:
        """创建阅读量统计DataFrame"""
        if stats and stats.get('total', 0) > 0:
            data = [
                {'统计项': '总阅读量', '数值': f"{stats.get('total', 0):,}"},
                {'统计项': '平均阅读量', '数值': f"{int(stats.get('average', 0)):,}"},
                {'统计项': '最高阅读量', '数值': f"{stats.get('max', 0):,}"},
                {'统计项': '最低阅读量', '数值': f"{stats.get('min', 0):,}"},
                {'统计项': '高关注度文章数', '数值': f"{stats.get('high_impact_count', 0)} 篇 (阅读量>5000)"},
            ]
            return pd.DataFrame(data)

        return pd.DataFrame()

    def _create_institution_stats_dataframe(self, analyses: List[Dict]) -> pd.DataFrame:
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

        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values('平均评分', ascending=False)

        return df

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

    def _format_worksheet(self, worksheet, df):
        """格式化工作表"""
        try:
            # 自动调整列宽
            for column in df.columns:
                column_length = max(
                    df[column].astype(str).map(len).max(),
                    len(str(column))
                )
                column_length = min(column_length + 2, 50)
                col_idx = df.columns.get_loc(column)
                if col_idx < 26:
                    column_letter = chr(65 + col_idx)
                    worksheet.column_dimensions[column_letter].width = column_length
        except Exception as e:
            self.logger.debug(f"格式化工作表失败: {e}")
