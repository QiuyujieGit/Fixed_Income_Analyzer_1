"""数据处理工具 - AI增强版本"""
import re
import json
from typing import List, Dict, Any, Tuple
import pandas as pd
from datetime import datetime
import logging
import numpy as np
from collections import Counter
from analyzer.prompt import (
    YIELD_PREDICTION_AGGREGATION_PROMPT,
    ENHANCED_SCORING_PROMPT,
    KEY_OPINIONS_EXTRACTION_PROMPT
)

class DataProcessor:
    """数据处理器 - AI增强版本"""

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

    def extract_yield_predictions_with_ai(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """TODO 3.1: 使用AI进行收益率预测聚合统计"""
        if not self.deepseek_client:
            self.logger.warning("DeepSeek客户端未初始化，使用基础方法")
            return self.extract_yield_predictions(analyses)

        # 准备预测数据
        predictions_data = []
        for analysis in analyses:
            prediction = {
                '机构': analysis.get('机构'),
                '评分': analysis.get('重要性评分'),
                '日期': analysis.get('日期'),
                '10Y预测': analysis.get('10Y国债收益率预测'),
                '5Y预测': analysis.get('5Y国债收益率预测'),
                '主要观点': analysis.get('整体观点', '')[:200]
            }
            predictions_data.append(prediction)

        prompt = YIELD_PREDICTION_AGGREGATION_PROMPT.format(
            predictions_data=json.dumps(predictions_data, ensure_ascii=False, indent=2)
        )

        try:
            response = self.deepseek_client.chat(prompt)
            result = json.loads(self._extract_json(response))

            # 添加统计信息
            result['total_institutions'] = len(analyses)
            result['analysis_date'] = datetime.now().strftime('%Y-%m-%d')

            return result
        except Exception as e:
            self.logger.error(f"AI收益率预测聚合失败: {e}")
            return self.extract_yield_predictions(analyses)

    def calculate_article_score_with_ai(self, analysis: Dict[str, Any], read_count: int = 0) -> Dict[str, Any]:
        """TODO 3.2 & 3.3: 使用AI进行增强评分（包含阅读量）"""
        if not self.deepseek_client:
            return self.calculate_article_score(analysis, read_count)

        # 准备内容摘要
        content_summary = self._create_content_summary(analysis)
        content_length = sum(len(str(analysis.get(key, ''))) for key in [
            '基本面及通胀', '资金面', '货币及财政政策', '机构行为', '海外及其他'
        ])

        prompt = ENHANCED_SCORING_PROMPT.format(
            institution=analysis.get('机构', ''),
            date=analysis.get('日期', ''),
            read_count=read_count,
            content_length=content_length,
            content_summary=content_summary
        )

        try:
            response = self.deepseek_client.chat(prompt)
            result = json.loads(self._extract_json(response))

            # 确保评分有区分度
            score = result.get('综合评分', 5)
            if 6.5 <= score <= 7.5:
                # 对于接近7分的，根据具体情况微调
                if read_count > 10000:
                    score += 0.5
                elif read_count < 1000:
                    score -= 0.5

            result['综合评分'] = round(score, 1)

            return {
                '重要性评分': result['综合评分'],
                '评分细项': result.get('维度评分', {}),
                '评分理由': result.get('评分理由', ''),
                '核心亮点': result.get('核心亮点', []),
                '不足之处': result.get('不足之处', []),
                '阅读量': read_count
            }
        except Exception as e:
            self.logger.error(f"AI评分失败: {e}")
            return self.calculate_article_score(analysis, read_count)

    def extract_key_opinions_with_ai(self, analyses: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, Any]:
        """TODO 3.4: 使用AI进行主要观点的NLP分析和提炼"""
        if not self.deepseek_client:
            return self.extract_key_opinions(analyses, top_n)

        # 准备文章摘要
        sorted_analyses = sorted(analyses, key=lambda x: x.get('重要性评分', 0), reverse=True)[:top_n]

        articles_summary = []
        for analysis in sorted_analyses:
            summary = {
                '机构': analysis.get('机构'),
                '日期': analysis.get('日期'),
                '评分': analysis.get('重要性评分'),
                '阅读量': analysis.get('阅读量', 0),
                '整体观点': analysis.get('整体观点', ''),
                '投资策略': analysis.get('投资策略', ''),
                '10Y预测': analysis.get('10Y国债收益率预测', {}).get('方向', ''),
                '关键内容': {
                    '基本面': self._extract_key_sentences(analysis.get('基本面及通胀', '')),
                    '资金面': self._extract_key_sentences(analysis.get('资金面', '')),
                    '政策面': self._extract_key_sentences(analysis.get('货币及财政政策', ''))
                }
            }
            articles_summary.append(summary)

        prompt = KEY_OPINIONS_EXTRACTION_PROMPT.format(
            articles_summary=json.dumps(articles_summary, ensure_ascii=False, indent=2)
        )

        try:
            response = self.deepseek_client.chat(prompt)
            result = json.loads(self._extract_json(response))

            # 确保篇幅控制
            for key in ['利率走势核心观点', '政策预期核心观点', '市场情绪核心观点', '投资策略核心观点']:
                if key in result and len(result[key]) > 200:
                    result[key] = result[key][:197] + '...'

            return result
        except Exception as e:
            self.logger.error(f"AI观点提取失败: {e}")
            return self.extract_key_opinions(analyses, top_n)

    def _create_content_summary(self, analysis: Dict[str, Any]) -> str:
        """创建内容摘要"""
        summary_parts = []

        for key in ['基本面及通胀', '资金面', '货币及财政政策', '投资策略']:
            content = analysis.get(key, '')
            if content:
                # 提取前200个字符
                summary_parts.append(f"{key}: {str(content)[:200]}...")

        return '\n'.join(summary_parts)

    def _extract_key_sentences(self, text: str, max_sentences: int = 3) -> List[str]:
        """提取关键句子"""
        if not text:
            return []

        # 简单的句子分割
        sentences = re.split(r'[。！？]', str(text))
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        # 返回前N个句子
        return sentences[:max_sentences]

    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON内容"""
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json_match.group()
        return text

    # ===== 基础方法（作为降级方案）=====

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
        """提取并聚合收益率预测（基础版本）"""
        predictions = {
            '10Y': {'上行': [], '下行': [], '震荡': [], '未涉及': []},
            '5Y': {'上行': [], '下行': [], '震荡': [], '未涉及': []}
        }

        for analysis in analyses:
            institution = analysis.get('机构', '未知')
            score = analysis.get('重要性评分', 0)

            # 处理10Y和5Y预测
            for term in ['10Y', '5Y']:
                forecast_key = f'{term}国债收益率预测'
                forecast = analysis.get(forecast_key, {})

                if isinstance(forecast, dict):
                    direction = forecast.get('方向', '未涉及')
                    classified_direction = self._classify_direction(direction)
                    predictions[term][classified_direction].append({
                        '机构': institution,
                        '评分': score,
                        '区间': forecast.get('区间', ''),
                        '概率': forecast.get('概率', '')
                    })

        # 计算统计
        summary = {}
        for term in ['10Y', '5Y']:
            total = sum(len(v) for v in predictions[term].values())
            if total > 0:
                summary[term] = {}
                for direction, institutions in predictions[term].items():
                    summary[term][direction] = {
                        'count': len(institutions),
                        'percentage': round(len(institutions) / total * 100, 1),
                        'avg_score': round(np.mean([i['评分'] for i in institutions]), 1) if institutions else 0,
                        'institutions': [i['机构'] for i in institutions]
                    }

        return summary

    def _classify_direction(self, direction: str) -> str:
        """分类预测方向"""
        if not direction:
            return '未涉及'

        direction = str(direction).lower()
        if any(word in direction for word in ['上', '升', '涨', '高']):
            return '上行'
        elif any(word in direction for word in ['下', '降', '跌', '低']):
            return '下行'
        elif any(word in direction for word in ['震荡', '区间', '横盘', '平稳']):
            return '震荡'
        else:
            return '未涉及'

    def calculate_article_score(self, analysis: Dict[str, Any], read_count: int = 0) -> Dict[str, Any]:
        """计算文章评分（基础版本）"""
        scores = {}

        # 1. 数据支撑度（25%）
        data_count = 0
        for dim in ['基本面及通胀', '资金面', '货币及财政政策']:
            content = analysis.get(dim, '')
            numbers = self.extract_numbers(str(content))
            data_count += len(numbers)

        scores['数据支撑'] = min(10, data_count * 0.5)

        # 2. 逻辑完整性（20%）
        complete_dims = 0
        for dim in ['基本面及通胀', '资金面', '货币及财政政策', '机构行为', '海外及其他']:
            if analysis.get(dim) and len(str(analysis.get(dim))) > 30:
                complete_dims += 1

        scores['逻辑完整'] = complete_dims * 2

        # 3. 策略可操作性（25%）
        strategy = str(analysis.get('投资策略', ''))
        if any(keyword in strategy for keyword in ['买入', '卖出', '增持', '减持', '配置']):
            scores['策略价值'] = 8
        elif '建议' in strategy:
            scores['策略价值'] = 6
        else:
            scores['策略价值'] = 4

        # 4. 观点独特性（15%）
        unique_score = 6
        analysis_str = str(analysis)
        if '首次' in analysis_str or '独家' in analysis_str:
            unique_score = 8
        elif '市场一致' in analysis_str or '共识' in analysis_str:
            unique_score = 4
        scores['观点独特'] = unique_score

        # 5. 市场影响力（15%）- TODO 3.2实现
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
            scores['市场影响'] = 5

        # 计算加权总分
        weights = {
            '数据支撑': 0.25,
            '逻辑完整': 0.20,
            '策略价值': 0.25,
            '观点独特': 0.15,
            '市场影响': 0.15
        }

        total_score = sum(scores[k] * weights[k] for k in scores)

        # 增加区分度
        if 6.5 <= total_score <= 7.5:
            # 根据具体情况调整
            if scores['数据支撑'] >= 8 and scores['策略价值'] >= 8:
                total_score += 0.5
            elif scores['数据支撑'] <= 4 or scores['策略价值'] <= 4:
                total_score -= 0.5

        return {
            '重要性评分': round(total_score, 1),
            '评分细项': scores,
            '评分理由': self._generate_score_reason(scores),
            '阅读量': read_count
        }

    def _generate_score_reason(self, scores: Dict[str, int]) -> str:
        """生成评分理由"""
        reasons = []

        if scores['数据支撑'] >= 8:
            reasons.append("数据支撑充分")
        elif scores['数据支撑'] <= 4:
            reasons.append("缺乏数据支撑")

        if scores['策略价值'] >= 8:
            reasons.append("策略建议明确可操作")
        elif scores['策略价值'] <= 4:
            reasons.append("策略建议模糊")

        if scores['市场影响'] >= 8:
            reasons.append("市场影响力大")

        return f"评分依据：{'; '.join(reasons)}。" + \
               f"详细：数据支撑{scores['数据支撑']}分，逻辑完整{scores['逻辑完整']}分，" + \
               f"策略价值{scores['策略价值']}分，观点独特{scores['观点独特']}分，" + \
               f"市场影响{scores['市场影响']}分。"

    def extract_key_opinions(self, analyses: List[Dict[str, Any]], top_n: int = 5) -> Dict[str, List[str]]:
        """提取主要观点（基础版本）"""
        key_opinions = {
            '利率走势': [],
            '政策预期': [],
            '市场情绪': [],
            '投资建议': []
        }

        sorted_analyses = sorted(analyses, key=lambda x: x.get('重要性评分', 0), reverse=True)[:top_n]

        for analysis in sorted_analyses:
            institution = analysis.get('机构', '')

            rate_opinion = analysis.get('整体观点', '')
            if rate_opinion:
                key_opinions['利率走势'].append(f"{institution}: {str(rate_opinion)[:100]}...")

            policy = analysis.get('货币及财政政策', '')
            if policy and len(str(policy)) > 30:
                key_opinions['政策预期'].append(f"{institution}: {str(policy)[:100]}...")

            sentiment = analysis.get('机构行为', '')
            if sentiment and len(str(sentiment)) > 30:
                key_opinions['市场情绪'].append(f"{institution}: {str(sentiment)[:100]}...")

            strategy = analysis.get('投资策略', '')
            if strategy:
                key_opinions['投资建议'].append(f"{institution}: {str(strategy)[:100]}...")

        return key_opinions

    def generate_opinion_cloud(self, analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """生成观点词云数据"""
        all_text = ""

        for analysis in analyses:
            for key in ['基本面及通胀', '资金面', '货币及财政政策', '整体观点', '投资策略']:
                all_text += str(analysis.get(key, '')) + " "

        # 提取关键词
        keywords = re.findall(r'[\u4e00-\u9fa5]+', all_text)

        # 过滤停用词
        stop_words = {'的', '了', '在', '是', '和', '与', '或', '等', '将', '会', '可能', '预计', '认为', '表示'}
        keywords = [w for w in keywords if len(w) >= 2 and w not in stop_words]

        # 统计词频
        word_freq = Counter(keywords)

        # 返回前50个高频词
        return dict(word_freq.most_common(50))

    def merge_analyses(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个分析结果，生成增强的统计信息"""
        if not analyses:
            return self._empty_merge_result()

        # 基础统计
        institutions = list(set(a.get('机构', '') for a in analyses if a.get('机构')))
        dates = [a.get('日期', '') for a in analyses if a.get('日期')]

        # 使用AI增强功能（如果可用）
        if self.deepseek_client:
            yield_predictions = self.extract_yield_predictions_with_ai(analyses)
            key_opinions = self.extract_key_opinions_with_ai(analyses)
        else:
            yield_predictions = self.extract_yield_predictions(analyses)
            key_opinions = self.extract_key_opinions(analyses)

        return {
            'total_count': len(analyses),
            'institutions': institutions,
            'date_range': self.parse_date_range(dates),
            'average_score': self._calculate_average_score(analyses),
            'score_distribution': self._calculate_score_distribution(analyses),
            'dimension_statistics': self._calculate_dimension_stats(analyses),
            'article_type_statistics': self._calculate_article_type_stats(analyses),
            'yield_predictions': yield_predictions,
            'key_opinions': key_opinions,
            'opinion_cloud': self.generate_opinion_cloud(analyses),
            'read_count_stats': self._calculate_read_count_stats(analyses)
        }

    def _calculate_score_distribution(self, analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """计算评分分布"""
        distribution = {
            '9-10分': 0,
            '7-8分': 0,
            '5-6分': 0,
            '3-4分': 0,
            '1-2分': 0
        }

        for analysis in analyses:
            score = analysis.get('重要性评分', 0)
            if score >= 9:
                distribution['9-10分'] += 1
            elif score >= 7:
                distribution['7-8分'] += 1
            elif score >= 5:
                distribution['5-6分'] += 1
            elif score >= 3:
                distribution['3-4分'] += 1
            else:
                distribution['1-2分'] += 1

        return distribution

    def _calculate_read_count_stats(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算阅读量统计"""
        read_counts = [a.get('阅读量', 0) for a in analyses if a.get('阅读量', 0) > 0]

        if not read_counts:
            return {
                'total': 0,
                'average': 0,
                'max': 0,
                'min': 0,
                'high_impact_count': 0
            }

        return {
            'total': sum(read_counts),
            'average': round(np.mean(read_counts), 0),
            'max': max(read_counts),
            'min': min(read_counts),
            'high_impact_count': len([r for r in read_counts if r >= 5000])
        }

    def _empty_merge_result(self) -> Dict[str, Any]:
        """返回空的合并结果"""
        return {
            'total_count': 0,
            'institutions': [],
            'date_range': '未知',
            'average_score': 0,
            'score_distribution': {},
            'dimension_statistics': {},
            'article_type_statistics': {},
            'yield_predictions': {},
            'key_opinions': {},
            'opinion_cloud': {},
            'read_count_stats': {}
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

    def _calculate_average_score(self, analyses: List[Dict[str, Any]]) -> float:
        """计算平均评分"""
        scores = [
            a.get('重要性评分', 0) for a in analyses
            if isinstance(a.get('重要性评分'), (int, float)) and a.get('重要性评分') > 0
        ]

        if not scores:
            return 0.0

        return round(sum(scores) / len(scores), 2)

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

    def _calculate_article_type_stats(self, analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计文章类型分布"""
        type_stats = {}

        for analysis in analyses:
            article_types = analysis.get('文章类型', [])
            if isinstance(article_types, list):
                for type_name in article_types:
                    type_stats[type_name] = type_stats.get(type_name, 0) + 1

        return type_stats

    def validate_analysis_result(self, analysis: Dict[str, Any]) -> bool:
        """验证分析结果的完整性"""
        # 必需字段
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
                self.logger.warning(f"分析结果缺少必需字段: {field}")
                return False

        # 检查评分是否合理
        score = analysis.get('重要性评分', 0)
        try:
            score = float(score)
            if score < 1 or score > 10:
                self.logger.warning(f"评分超出范围: {score}")
                return False
        except (TypeError, ValueError):
            self.logger.warning(f"评分格式错误: {score}")
            return False

        # 检查收益率预测格式
        for key in ['10Y国债收益率预测', '5Y国债收益率预测']:
            forecast = analysis.get(key, {})
            if not isinstance(forecast, dict):
                self.logger.warning(f"{key}格式错误，应为字典")
                return False

        return True
