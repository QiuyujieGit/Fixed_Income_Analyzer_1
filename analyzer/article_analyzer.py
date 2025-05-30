"""文章分析器 - 简化版"""
import json
import re
from typing import Dict, Any
from api.deepseek_client import DeepSeekClient
from analyzer.prompt import ARTICLE_ANALYSIS_PROMPT
from config.setting import ANALYSIS_DIMENSIONS


class ArticleAnalyzer:
    """文章分析器"""

    def __init__(self, deepseek_client: DeepSeekClient):
        self.client = deepseek_client
        self.dimensions = ANALYSIS_DIMENSIONS

    def analyze(self, content: str, url: str, institution: str = "", date: str = "") -> Dict[str, Any]:
        """分析单篇文章 - 简化版"""
        if len(content) > 10000:
            content = content[:10000] + "..."

        prompt = ARTICLE_ANALYSIS_PROMPT.format(
            institution=institution,
            date=date,
            content=content[:5000]
        )

        response = self.client.chat(prompt)

        try:
            # 提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response)

            # 添加元数据
            result['url'] = url
            result['机构'] = institution
            result['日期'] = str(date)

            return result

        except Exception as e:
            return self._get_default_analysis(url, institution, date)

    def _get_default_analysis(self, url: str, institution: str, date: str) -> Dict[str, Any]:
        """返回默认分析结果 - 简化版"""
        return {
            "url": url,
            "机构": institution,
            "日期": str(date),
            "基本面及通胀": "",
            "资金面": "",
            "货币及财政政策": "",
            "机构行为": "",
            "海外及其他": "",
            "10Y国债态度": "文章未涉及",
            "10Y预测区间": "文章未涉及",
            "5Y国债态度": "文章未涉及",
            "5Y预测区间": "文章未涉及",
            "整体观点": "分析失败"
        }
