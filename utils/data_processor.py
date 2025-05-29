"""数据处理工具 - 更新版本"""
import re
import json
from typing import List, Dict, Any, Tuple
import pandas as pd
from datetime import datetime
import logging
import numpy as np
from collections import Counter

class DataProcessor:
    """数据处理器 - 增强版本"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本"""
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
        """从文本中提取数字"""
        if not text:
            return []

        # 匹配各种格式的数字
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

    @staticmethod
    def extract_yield_predictions(analyses: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """提取并聚合收益率预测（TODO 3.1）"""
        predictions = {
            '10Y': {'上行': [], '下行': [], '震荡': [], '未涉及': []},
            '5Y': {'上行': [], '下行': [], '震荡': [], '未涉及': []}
        }

        for analysis in analyses:
            institution = analysis.get('机构', '未知')
            score = analysis.get('重要性评分', 0)

            # 10Y预测
            forecast_10y = analysis.get('10Y国债收益率预测', {})
            if isinstance(forecast_10y, dict):
                direction = forecast_10y.get('方向', '未涉及')
                predictions['10Y'][self._classify_direction(direction)].append({
                    '机构': institution,
                    '评分': score,
                    '区间': forecast_10y.get('区间', ''),
                    '概率': forecast_10y.get('概率', '')
                })

            # 5Y预测
            forecast_5y = analysis.get('5Y国债收益率预测', {})
            if isinstance(forecast_5y, dict):
                direction = forecast_5y.get('方向', '未涉及')
                predictions['5Y'][self._classify_direction(direction)].append({
                    '机构': institution,
                    '评分': score,
                    '区间': forecast_5y.get('区间', ''),
                    '概率': forecast_5y.get('概率', '')
                })

        # 计算聚合统计
        summary = {}
        for term in ['10Y', '5Y']:
            total = sum(len(v) for v in predictions[term].values())
            if total > 0:
                summary[term] = {
                    direction: {
                        'count': len(institutions),
                        'percentage': len(institutions) / total * 100,
                        'avg_score': np.mean([i['评分'] for i in institutions]) if institutions else 0,
                        'institutions': [i['机构'] for i in institutions]
                    }
                    for direction, institutions in predictions[term].items()
                }
            else:
                summary[term] = {}

        return summary

    @staticmethod
    def _classify_direction(direction: str) -> str:
        """分类预测方向"""
        if '上' in direction or '升' in direction:
            return '上行'
        elif '下' in direction or '降' in direction:
            return '下行'
        elif '震荡' in direction or '区间' in direction:
            return '震荡'
        else:
            return '未涉及'

    @staticmethod
    def calculate_article_score(analysis: Dict[str, Any], read_count: int = 0) -> Dict[str, Any]:
        """计算文章评分（TODO 3.2 & 3.3）"""
        scores = {}

        # 1. 数据支撑度（25%）
        data_count = 0
        for dim in ['基本面及通胀', '资金面', '货币及财政政策']:
            content = analysis.get(dim, '')
            # 统计数字和百分比
            numbers = DataProcessor.extract_numbers(content)
            data_count += len(numbers)

        scores['数据支撑'] = min(10, data_count * 0.5)

        # 2. 逻辑完整性（20%）
        complete_dims = 0
        for dim in ['基本面及通胀', '资金面', '货币及财政政策', '机构行为', '海外及其他']:
            if analysis.get(dim) and len(str(analysis.get(dim))) > 30:
                complete_dims += 1

        scores['逻辑完整'] = complete_dims * 2

        # 3. 策略可操作性（25%）
        strategy = analysis.get('投资策略', '')
        if '具体' in strategy or '建议' in strategy:
            if any(keyword in strategy for keyword in ['买入', '卖出', '增持', '减持', '配置']):
                scores['策略价值'] = 8
            else:
                scores['策略价值'] = 6
        else:
            scores['策略价值'] = 4

        # 4. 观点独特性（15%）
        unique_score = 6  # 基础分
        if '首次' in str(analysis) or '独家' in str(analysis):
            unique_score = 8
        elif '市场一致' in str(analysis) or '共识' in str(analysis):
            unique_score = 4
        scores['观点独特'] = unique_score

        # 5. 阅读量影响（15%）- TODO 3.2新增
        if read_count > 0:
            if read_count >= 10000:
                scores['市场影响'] = 10
            elif read_count >= 5000:
                scores['市场影响'] = 8
            elif read_count >= 1000:
                scores['市场影响'] = 6
            else:
                scores['市场影响'] = 4
        else:
            scores['市场影响'] = 5  # 无数据时给中等分

        # 计算加权总分
        weights = {
            '数据支撑': 0.25,
            '逻辑完整': 0.20,
            '策略价值': 0.25,
            '观点独特': 0.15,
            '市场影响': 0.15
        }

        total_score = sum(scores[k] * weights[k] for k in scores)

        return {
            '重要性评分': round(total_score, 1),
            '评分细项': scores,
            '评分理由': f"数据支撑{scores['数据支撑']}分，逻辑完整性{scores['逻辑完整']}分，策略价值{scores['策略价值']}分，观点独特性{scores['观点独特']}分，市场影响力{scores['市场影响']}分"
        }

    @staticmethod
    def extract_key_opinions(analyses: List[Dict[str, Any]], top_n: int = 5) -> Dict[str, List[str]]:
        """提取主要观点（TODO 3.4）"""
        key_opinions = {
            '利率走势': [],
            '政策预期': [],
            '市场情绪': [],
            '投资建议': []
        }

        # 按评分排序，取前N个高质量分析
        sorted_analyses = sorted(analyses, key=lambda x: x.get('重要性评分', 0), reverse=True)[:top_n]

        for analysis in sorted_analyses:
            institution = analysis.get('机构', '')

            # 提取利率走势观点
            rate_opinion = analysis.get('整体观点', '')
            if rate_opinion:
                key_opinions['利率走势'].append(f"{institution}: {rate_opinion[:100]}...")

            # 提取政策预期
            policy = analysis.get('货币及财政政策', '')
            if policy and len(policy) > 30:
                key_opinions['政策预期'].append(f"{institution}: {policy[:100]}...")

            # 提取市场情绪
            sentiment = analysis.get('机构行为', '')
            if sentiment and len(sentiment) > 30:
                key_opinions['市场情绪'].append(f"{institution}: {sentiment[:100]}...")

            # 提取投资建议
            strategy = analysis.get('投资策略', '')
            if strategy:
                key_opinions['投资建议'].append(f"{institution}: {strategy[:100]}...")

        return key_opinions

    @staticmethod
    def generate_opinion_cloud(analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """生成观点词云数据"""
        all_text = ""

        # 收集所有文本
        for analysis in analyses:
            for key in ['基本面及通胀', '资金面', '货币及财政政策', '整体观点', '投资策略']:
                all_text += str(analysis.get(key, '')) + " "

        # 提取关键词
        keywords = re.findall(r'[\u4e00-\u9fa5]+', all_text)

        # 过滤停用词
        stop_words = {'的', '了', '在', '是', '和', '与', '或', '等', '将', '会', '可能', '预计'}
        keywords = [w for w in keywords if len(w) >= 2 and w not in stop_words]

        # 统计词频
        word_freq = Counter(keywords)

        # 返回前50个高频词
        return dict(word_freq.most_common(50))

    @staticmethod
    def parse_date(date_str: str) -> str:
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

    @staticmethod
    def merge_analyses(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个分析结果，生成增强的统计信息"""
        if not analyses:
            return {
                'total_count': 0,
                'institutions': [],
                'date_range': '未知',
                'average_score': 0,
                'dimension_statistics': {},
                'yield_predictions': {},
                'key_opinions': {}
            }

        # 基础统计
        institutions = list(set(a.get('机构', '') for a in analyses if a.get('机构')))
        dates = [a.get('日期', '') for a in analyses if a.get('日期')]
        date_range = DataProcessor.parse_date_range(dates)

        # 增强统计
        return {
            'total_count': len(analyses),
            'institutions': institutions,
            'date_range': date_range,
            'average_score': DataProcessor._calculate_average_score(analyses),
            'dimension_statistics': DataProcessor._calculate_dimension_stats(analyses),
            'article_type_statistics': DataProcessor._calculate_article_type_stats(analyses),
            'yield_predictions': DataProcessor.extract_yield_predictions(analyses),
            'key_opinions': DataProcessor.extract_key_opinions(analyses),
            'opinion_cloud': DataProcessor.generate_opinion_cloud(analyses)
        }

    @staticmethod
    def parse_date_range(dates: List[str]) -> str:
        """解析日期范围"""
        if not dates:
            return "未知"

        valid_dates = []
        for date in dates:
            parsed = DataProcessor.parse_date(date)
            if parsed and parsed != date:
                valid_dates.append(parsed)

        if not valid_dates:
            return "未知"

        valid_dates.sort()

        if len(valid_dates) == 1:
            return valid_dates[0]
        else:
            return f"{valid_dates[0]} 至 {valid_dates[-1]}"

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
