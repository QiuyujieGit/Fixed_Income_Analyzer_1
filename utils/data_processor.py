"""数据处理工具 - 简化版本"""
import re
import json
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
import logging
from collections import Counter


class DataProcessor:
    """数据处理器 - 简化版本"""

    def __init__(self, deepseek_client=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.deepseek_client = deepseek_client

    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""

        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()

        return text

    def extract_numbers(self, text: str) -> List[float]:
        """从文本中提取数字"""
        if not text:
            return []

        pattern = r'[-+]?\d+\.?\d*%?'
        matches = re.findall(pattern, text)

        numbers = []
        for match in matches:
            try:
                if match.endswith('%'):
                    num = float(match[:-1]) / 100
                else:
                    num = float(match)
                numbers.append(num)
            except ValueError:
                continue

        return numbers

    def extract_yield_predictions(self, analyses: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """提取收益率预测态度统计"""
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

    def merge_analyses(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个分析结果，生成统计信息"""
        if not analyses:
            return self._empty_merge_result()

        # 基础统计
        institutions = list(set(a.get('机构', '') for a in analyses if a.get('机构')))
        dates = [a.get('日期', '') for a in analyses if a.get('日期')]

        return {
            'total_count': len(analyses),
            'article_count': len(analyses),  # 添加article_count
            'institutions': institutions,
            'date_range': self.parse_date_range(dates),
            'dimension_statistics': self._calculate_dimension_stats(analyses),
            'yield_predictions': self.extract_yield_predictions(analyses),
        }

    def _empty_merge_result(self) -> Dict[str, Any]:
        """返回空的合并结果"""
        return {
            'total_count': 0,
            'article_count': 0,
            'institutions': [],
            'date_range': '未知',
            'dimension_statistics': {},
            'yield_predictions': {},
            'key_opinions': {},
            'opinion_cloud': {}
        }

    def parse_date(self, date_str: str) -> str:
        """解析并标准化日期"""
        if not date_str or pd.isna(date_str):
            return ""

        date_str = str(date_str).strip()

        # 尝试多种日期格式
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y.%m.%d',
            '%Y年%m月%d日',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y%m%d'
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return date_str

    def parse_date_range(self, dates: List[str]) -> str:
        """解析日期范围"""
        if not dates:
            return "未知"

        valid_dates = []
        for date in dates:
            parsed = self.parse_date(date)
            if parsed and '-' in parsed:
                valid_dates.append(parsed)

        if not valid_dates:
            return "未知"

        valid_dates.sort()

        if len(valid_dates) == 1:
            return valid_dates[0]
        else:
            return f"{valid_dates[0]} 至 {valid_dates[-1]}"

    def _calculate_dimension_stats(self, analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计各维度出现次数"""
        dimensions = [
            '基本面及通胀',
            '资金面',
            '货币及财政政策',
            '机构行为',
            '海外及其他'
        ]

        stats = {dim: 0 for dim in dimensions}

        for analysis in analyses:
            for dim in dimensions:
                content = analysis.get(dim, '')
                if content and len(str(content).strip()) > 10:
                    stats[dim] += 1

        return stats
