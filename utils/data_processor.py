"""数据处理工具"""
import re
import json
from typing import List, Dict, Any, Tuple
import pandas as pd
from datetime import datetime
import logging


class DataProcessor:
    """数据处理器"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""

        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)

        # 移除特殊字符
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        # 移除多余的换行
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 移除首尾空白
        text = text.strip()

        return text

    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """从文本中提取数字

        Args:
            text: 包含数字的文本

        Returns:
            List[float]: 提取的数字列表
        """
        if not text:
            return []

        # 匹配各种格式的数字
        # 支持：整数、小数、百分比、负数
        pattern = r'[-+]?\d+\.?\d*%?'
        matches = re.findall(pattern, text)

        numbers = []
        for match in matches:
            try:
                # 处理百分号
                if match.endswith('%'):
                    num = float(match[:-1]) / 100
                else:
                    num = float(match)
                numbers.append(num)
            except ValueError:
                continue

        return numbers

    @staticmethod
    def extract_yield_range(text: str) -> Tuple[float, float]:
        """从文本中提取收益率区间

        Args:
            text: 包含收益率的文本

        Returns:
            Tuple[float, float]: (最小值, 最大值)
        """
        # 匹配形如 "2.30%-2.40%" 的模式
        pattern = r'(\d+\.?\d*)%?\s*[-~至到]\s*(\d+\.?\d*)%?'
        match = re.search(pattern, text)

        if match:
            try:
                min_val = float(match.group(1))
                max_val = float(match.group(2))

                # 如果数值大于10，可能是基点表示，转换为百分比
                if min_val > 10:
                    min_val = min_val / 100
                if max_val > 10:
                    max_val = max_val / 100

                return (min_val, max_val)
            except ValueError:
                pass

        return (None, None)

    @staticmethod
    def parse_date(date_str: str) -> str:
        """解析并标准化日期

        Args:
            date_str: 日期字符串

        Returns:
            str: 标准化的日期字符串 (YYYY-MM-DD)
        """
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

        # 如果都不匹配，返回原始字符串
        return date_str

    @staticmethod
    def parse_date_range(dates: List[str]) -> str:
        """解析日期范围

        Args:
            dates: 日期列表

        Returns:
            str: 日期范围描述
        """
        if not dates:
            return "未知"

        # 过滤有效日期
        valid_dates = []
        for date in dates:
            parsed = DataProcessor.parse_date(date)
            if parsed and parsed != date:  # 成功解析
                valid_dates.append(parsed)

        if not valid_dates:
            return "未知"

        # 排序
        valid_dates.sort()

        if len(valid_dates) == 1:
            return valid_dates[0]
        else:
            return f"{valid_dates[0]} 至 {valid_dates[-1]}"

    @staticmethod
    def merge_analyses(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个分析结果，生成统计信息

        Args:
            analyses: 分析结果列表

        Returns:
            Dict: 合并后的统计结果
        """
        if not analyses:
            return {
                'total_count': 0,
                'institutions': [],
                'date_range': '未知',
                'average_score': 0,
                'dimension_statistics': {}
            }

        # 提取机构列表
        institutions = list(set(
            a.get('机构', '') for a in analyses
            if a.get('机构')
        ))

        # 提取日期范围
        dates = [
            a.get('日期', '') for a in analyses
            if a.get('日期')
        ]
        date_range = DataProcessor.parse_date_range(dates)

        # 计算平均分
        average_score = DataProcessor._calculate_average_score(analyses)

        # 统计维度信息
        dimension_stats = DataProcessor._calculate_dimension_stats(analyses)

        # 统计文章类型
        article_type_stats = DataProcessor._calculate_article_type_stats(analyses)

        # 统计收益率预测
        yield_stats = DataProcessor._calculate_yield_stats(analyses)

        return {
            'total_count': len(analyses),
            'institutions': institutions,
            'date_range': date_range,
            'average_score': average_score,
            'dimension_statistics': dimension_stats,
            'article_type_statistics': article_type_stats,
            'yield_predictions': yield_stats
        }

    @staticmethod
    def _calculate_average_score(analyses: List[Dict[str, Any]]) -> float:
        """计算平均评分"""
        scores = [
            a.get('重要性评分', 0) for a in analyses
            if isinstance(a.get('重要性评分'), (int, float))
        ]

        if not scores:
            return 0.0

        return round(sum(scores) / len(scores), 2)

    @staticmethod
    def _calculate_dimension_stats(analyses: List[Dict[str, Any]]) -> Dict[str, int]:
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
                # 判断内容是否有效（长度大于10个字符）
                if content and len(str(content).strip()) > 10:
                    stats[dim] += 1

        return stats

    @staticmethod
    def _calculate_article_type_stats(analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计文章类型分布"""
        type_stats = {}

        for analysis in analyses:
            article_types = analysis.get('文章类型', [])
            if isinstance(article_types, list):
                for type_name in article_types:
                    type_stats[type_name] = type_stats.get(type_name, 0) + 1

        return type_stats

    @staticmethod
    def _calculate_yield_stats(analyses: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """统计收益率预测方向"""
        stats = {
            '10Y': {'上行': 0, '下行': 0, '震荡': 0, '未涉及': 0},
            '5Y': {'上行': 0, '下行': 0, '震荡': 0, '未涉及': 0}
        }

        for analysis in analyses:
            # 10Y预测
            forecast_10y = analysis.get('10Y国债收益率预测', {})
            if isinstance(forecast_10y, dict):
                direction = forecast_10y.get('方向', '未涉及')
                if '上' in direction:
                    stats['10Y']['上行'] += 1
                elif '下' in direction:
                    stats['10Y']['下行'] += 1
                elif '震荡' in direction:
                    stats['10Y']['震荡'] += 1
                else:
                    stats['10Y']['未涉及'] += 1

            # 5Y预测
            forecast_5y = analysis.get('5Y国债收益率预测', {})
            if isinstance(forecast_5y, dict):
                direction = forecast_5y.get('方向', '未涉及')
                if '上' in direction:
                    stats['5Y']['上行'] += 1
                elif '下' in direction:
                    stats['5Y']['下行'] += 1
                elif '震荡' in direction:
                    stats['5Y']['震荡'] += 1
                else:
                    stats['5Y']['未涉及'] += 1

        return stats

    @staticmethod
    def format_number(number: float, decimals: int = 2) -> str:
        """格式化数字显示

        Args:
            number: 数字
            decimals: 小数位数

        Returns:
            str: 格式化后的字符串
        """
        if pd.isna(number):
            return ""

        try:
            number = float(number)
            if abs(number) >= 1e9:
                return f"{number / 1e9:.{decimals}f}B"
            elif abs(number) >= 1e6:
                return f"{number / 1e6:.{decimals}f}M"
            elif abs(number) >= 1e3:
                return f"{number / 1e3:.{decimals}f}K"
            else:
                return f"{number:.{decimals}f}"
        except:
            return str(number)

    @staticmethod
    def format_percentage(value: float, decimals: int = 1) -> str:
        """格式化百分比

        Args:
            value: 数值（0-1之间表示百分比，大于1表示百分数）
            decimals: 小数位数

        Returns:
            str: 格式化后的百分比字符串
        """
        if pd.isna(value):
            return ""

        try:
            value = float(value)
            # 如果值在0-1之间，认为是小数形式的百分比
            if 0 <= abs(value) <= 1:
                return f"{value * 100:.{decimals}f}%"
            else:
                return f"{value:.{decimals}f}%"
        except:
            return str(value)

    @staticmethod
    def validate_analysis_result(analysis: Dict[str, Any]) -> bool:
        """验证分析结果的完整性

        Args:
            analysis: 分析结果字典

        Returns:
            bool: 是否有效
        """
        required_fields = [
            '机构', '日期', 'url',
            '基本面及通胀', '资金面',
            '货币及财政政策', '机构行为',
            '海外及其他', '整体观点',
            '投资策略', '重要性评分'
        ]

        # 检查必需字段
        for field in required_fields:
            if field not in analysis:
                return False

        # 检查评分是否合理
        score = analysis.get('重要性评分', 0)
        if not isinstance(score, (int, float)) or score < 1 or score > 10:
            return False

        # 检查收益率预测格式
        for key in ['10Y国债收益率预测', '5Y国债收益率预测']:
            forecast = analysis.get(key, {})
            if not isinstance(forecast, dict):
                return False

        return True