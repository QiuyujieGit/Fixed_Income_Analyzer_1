"""Excel报告生成器 - 简化版"""
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from config.setting import OUTPUT_DIR
from utils.logger import setup_logger


class ExcelGenerator:
    """Excel报告生成器"""

    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.logger = setup_logger("ExcelGenerator")

    def generate_report(self, analyses: List[Dict[str, Any]], timestamp: str) -> str:
        """生成简化版Excel报告"""
        try:
            excel_path = os.path.join(self.output_dir, f'债券市场分析结果_{timestamp}.xlsx')

            # 准备数据
            # 1. 主要分析结果
            main_df = self._create_main_dataframe(analyses)

            # 2. 态度统计
            attitude_df = self._create_attitude_statistics_dataframe(analyses)

            # 写入Excel
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                main_df.to_excel(writer, sheet_name='分析结果', index=False)
                attitude_df.to_excel(writer, sheet_name='态度统计', index=False)

            return excel_path

        except Exception as e:
            self.logger.error(f"生成Excel报告失败: {e}")
            return ""

    def _create_main_dataframe(self, analyses):
        """创建主要分析结果DataFrame - 简化版"""
        data = []

        for i, analysis in enumerate(analyses, 1):
            row = {
                '序号': i,
                '机构': analysis.get('机构', ''),
                '发布日期': analysis.get('日期', ''),
                '基本面及通胀': str(analysis.get('基本面及通胀', ''))[:300],
                '资金面': str(analysis.get('资金面', ''))[:300],
                '货币及财政政策': str(analysis.get('货币及财政政策', ''))[:300],
                '机构行为': str(analysis.get('机构行为', ''))[:300],
                '海外及其他': str(analysis.get('海外及其他', ''))[:300],
                '10Y国债态度': analysis.get('10Y国债态度', ''),
                '10Y预测区间': analysis.get('10Y预测区间', ''),
                '5Y国债态度': analysis.get('5Y国债态度', ''),
                '5Y预测区间': analysis.get('5Y预测区间', ''),
                '整体观点': analysis.get('整体观点', '')
            }
            data.append(row)

        return pd.DataFrame(data)

    def _create_attitude_statistics_dataframe(self, analyses):
        """创建态度统计DataFrame"""
        # 统计各态度数量
        stats = {
            '10Y看多': 0, '10Y看空': 0, '10Y中性': 0,
            '5Y看多': 0, '5Y看空': 0, '5Y中性': 0
        }

        institutions_by_attitude = {
            '10Y看多': [], '10Y看空': [], '10Y中性': [],
            '5Y看多': [], '5Y看空': [], '5Y中性': []
        }

        for analysis in analyses:
            inst = analysis.get('机构', '')

            # 10Y态度
            attitude_10y = analysis.get('10Y国债态度', '')
            if '多' in attitude_10y:
                stats['10Y看多'] += 1
                institutions_by_attitude['10Y看多'].append(inst)
            elif '空' in attitude_10y:
                stats['10Y看空'] += 1
                institutions_by_attitude['10Y看空'].append(inst)
            elif '中性' in attitude_10y or '震荡' in attitude_10y:
                stats['10Y中性'] += 1
                institutions_by_attitude['10Y中性'].append(inst)

            # 5Y态度（类似处理）
            attitude_5y = analysis.get('5Y国债态度', '')
            if '多' in attitude_5y:
                stats['5Y看多'] += 1
                institutions_by_attitude['5Y看多'].append(inst)
            elif '空' in attitude_5y:
                stats['5Y看空'] += 1
                institutions_by_attitude['5Y看空'].append(inst)
            elif '中性' in attitude_5y or '震荡' in attitude_5y:
                stats['5Y中性'] += 1
                institutions_by_attitude['5Y中性'].append(inst)

        # 构建DataFrame
        data = []
        for key, count in stats.items():
            data.append({
                '类别': key,
                '数量': count,
                '占比': f"{count / len(analyses) * 100:.1f}%" if analyses else "0%",
                '机构列表': ', '.join(institutions_by_attitude[key][:5]) +
                            (f'等{count}家' if count > 5 else '')
            })

        return pd.DataFrame(data)
