"""市场综合分析器"""
import json
from typing import List, Dict, Any
from api.deepseek_client import DeepSeekClient
from analyzer.prompt import YIELD_FORECAST_PROMPT, SUMMARY_REPORT_PROMPT
from config.setting import ANALYSIS_DIMENSIONS


class MarketAnalyzer:
    """市场综合分析器"""

    def __init__(self, deepseek_client: DeepSeekClient):
        self.client = deepseek_client
        self.dimensions = ANALYSIS_DIMENSIONS

    def generate_summary(self, analyses: List[Dict[str, Any]]) -> str:
        """生成市场总结报告"""
        # 按重要性排序
        sorted_analyses = sorted(analyses, key=lambda x: x.get('重要性评分', 0), reverse=True)

        # 整理详细观点
        detailed_views = self._extract_detailed_views(sorted_analyses[:5])

        # 统计文章类型
        article_types = self._count_article_types(analyses)

        # 生成收益率预测
        yield_forecast = self._generate_yield_forecast(analyses)

        # 构建提示词
        prompt = SUMMARY_REPORT_PROMPT.format(
            article_types=json.dumps(article_types, ensure_ascii=False),
            fundamental_views=json.dumps(detailed_views['基本面及通胀'][:2], ensure_ascii=False),
            liquidity_views=json.dumps(detailed_views['资金面'][:2], ensure_ascii=False),
            policy_views=json.dumps(detailed_views['货币及财政政策'][:2], ensure_ascii=False),
            institutional_views=json.dumps(detailed_views['机构行为'][:2], ensure_ascii=False),
            overseas_views=json.dumps(detailed_views['海外及其他'][:2], ensure_ascii=False),
            yield_forecast=yield_forecast
        )

        # 生成报告
        report = self.client.chat(prompt)

        # 清理格式
        report = self._clean_format(report)

        return report

    def _extract_detailed_views(self, analyses: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """提取详细观点"""
        detailed_views = {dim: [] for dim in self.dimensions}

        for analysis in analyses:
            for dim in self.dimensions:
                if analysis.get(dim) and len(analysis.get(dim, '')) > 20:
                    detailed_views[dim].append({
                        '机构': analysis.get('机构', ''),
                        '观点': analysis.get(dim)
                    })

        return detailed_views

    def _count_article_types(self, analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计文章类型"""
        article_types = {}

        for analysis in analyses:
            for type_name in analysis.get('文章类型', []):
                article_types[type_name] = article_types.get(type_name, 0) + 1

        return article_types

    def _generate_yield_forecast(self, analyses: List[Dict[str, Any]]) -> str:
        """生成收益率预测"""
        # 分离有效预测
        explicit_10y = []
        directional_10y = []
        explicit_5y = []
        directional_5y = []

        for analysis in analyses:
            # 处理10Y预测
            forecast_10y = analysis.get('10Y国债收益率预测', {})
            if isinstance(forecast_10y, dict):
                if forecast_10y.get('区间') and forecast_10y.get('区间') != '文章未涉及':
                    explicit_10y.append({
                        '机构': analysis.get('机构'),
                        '预测': forecast_10y
                    })
                elif forecast_10y.get('方向') and forecast_10y.get('方向') != '文章未涉及':
                    directional_10y.append({
                        '机构': analysis.get('机构'),
                        '方向': forecast_10y.get('方向')
                    })

            # 处理5Y预测
            forecast_5y = analysis.get('5Y国债收益率预测', {})
            if isinstance(forecast_5y, dict):
                if forecast_5y.get('区间') and forecast_5y.get('区间') != '文章未涉及':
                    explicit_5y.append({
                        '机构': analysis.get('机构'),
                        '预测': forecast_5y
                    })
                elif forecast_5y.get('方向') and forecast_5y.get('方向') != '文章未涉及':
                    directional_5y.append({
                        '机构': analysis.get('机构'),
                        '方向': forecast_5y.get('方向')
                    })

        # 构建预测提示词
        prompt = YIELD_FORECAST_PROMPT.format(
            explicit_10y=json.dumps(explicit_10y[:5], ensure_ascii=False),
            directional_10y=json.dumps(directional_10y[:5], ensure_ascii=False),
            explicit_5y=json.dumps(explicit_5y[:5], ensure_ascii=False),
            directional_5y=json.dumps(directional_5y[:5], ensure_ascii=False)
        )

        return self.client.chat(prompt)

    def _clean_format(self, text: str) -> str:
        """清理文本格式"""
        # 移除markdown标记
        text = text.replace('**', '').replace('##', '').replace('###', '')
        text = text.replace('```', '').replace('`', '')

        # 移除多余空行
        lines = text.split('\n')
        cleaned_lines = []
        prev_empty = False

        for line in lines:
            line = line.strip()
            if not line:
                if not prev_empty:
                    cleaned_lines.append('')
                    prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False

        return '\n'.join(cleaned_lines).strip()