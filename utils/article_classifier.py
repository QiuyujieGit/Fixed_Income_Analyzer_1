# utils/article_classifier.py
"""文章分类器 - 统一管理文章分类逻辑"""
from typing import Dict, List


class ArticleClassifier:
    """文章分类器"""

    def __init__(self):
        # 定义各类别的关键词和权重
        self.keywords = {
            '固收类': {
                '强特征': ['债','债券', '利率债', '信用债', '固定收益', '债市', '收益率曲线',
                           '久期', '凸性', '国债', '地方债', '企业债', '可转债', '城投债',
                           '金融债', '公司债', '短融', '中票', '永续债', '转债','可转债'],
                '一般特征': ['利率', '收益率', 'MLF', 'LPR', '央行', '流动性', '资金面',
                             '货币政策', '公开市场', '逆回购', '信用利差', '期限利差',
                             'DR007', 'R007', '资金价格', '债券配置', '利差'],
                '权重': 1.5
            },
            '权益类': {
                '强特征': ['股票', '股市', 'A股', '港股', '美股', '个股', '板块',
                           '涨停', '跌停', '龙头股', '题材股', '概念股', '创业板',
                           '科创板', '主板', '北交所'],
                '一般特征': ['指数', '涨跌', '成交量', '换手率', '市盈率', '估值',
                             '主力', '游资', '北向资金', '融资融券', '股价', '涨幅',
                             '跌幅', '技术分析', 'K线'],
                '权重': 1.0
            },
            '宏观类': {
                '强特征': ['宏观经济', 'GDP', '经济增长', '通货膨胀', '失业率',
                           '贸易战', '经济周期', '产业政策', '经济数据', '经济指标'],
                '一般特征': ['CPI', 'PPI', 'PMI', '工业增加值', '社融', '货币供应',
                             '进出口', '消费', '投资', '财政政策', 'M1', 'M2',
                             '社会消费品零售', '固定资产投资'],
                '权重': 1.5
            }
        }

        # 机构类型映射
        self.institution_types = {
            '固收类': ['固收', '债券', '利率', '信用', '固定收益','债市'],
            '权益类': ['股票', '权益', '策略', '量化', '股市'],
            '综合类': ['证券', '研究', '宏观', '策略', '金融']
        }

    def classify(self, title: str, institution: str = "", content: str = "",
                 content_type: str = "") -> str:
        """分类文章

        Args:
            title: 文章标题
            institution: 机构名称
            content: 文章内容（前500字）
            content_type: 预设的内容类型（如果有）

        Returns:
            文章类型：固收类、权益类、宏观类、其他
        """
        # 如果有预设的内容类型，优先使用
        if content_type:
            if '固收' in content_type or '债' in content_type:
                return '固收类'
            elif '权益' in content_type or '股' in content_type:
                return '权益类'
            elif '宏观' in content_type:
                return '宏观类'

        # 合并所有文本进行分析
        full_text = f"{title} {institution} {content}".lower()

        # 如果文本太短，返回其他
        if len(full_text) < 20:
            return '其他'

        # 计算各类别得分
        scores = {}

        for category, keywords_dict in self.keywords.items():
            score = 0

            # 强特征匹配
            for keyword in keywords_dict['强特征']:
                if keyword.lower() in full_text:
                    score += 2 * keywords_dict['权重']

            # 一般特征匹配
            for keyword in keywords_dict['一般特征']:
                if keyword.lower() in full_text:
                    score += 1 * keywords_dict['权重']

            # 机构名称加权
            for inst_keyword in self.institution_types.get(category.replace('类', ''), []):
                if inst_keyword.lower() in institution.lower():
                    score += 1.5

            scores[category] = score

        # 如果没有明显特征，返回其他
        if max(scores.values()) < 2:
            return '其他'

        # 返回得分最高的类别
        return max(scores, key=scores.get)

    def is_relevant_article(self, title: str, digest: str, content_type: str) -> bool:
        """判断文章是否相关（用于爬虫筛选）"""
        # 排除词
        exclude_keywords = ['招聘', '培训', '广告', '活动', '会议', '年会', '福利',
                            '招标', '中标', '公告', '声明', '澄清']

        text = (title + digest).lower()

        # 检查排除词
        for keyword in exclude_keywords:
            if keyword in text:
                return False

        # 检查是否包含相关关键词
        article_type = self.classify(title, "", digest, content_type)

        # 只要不是"其他"类型，就认为是相关的
        return article_type != '其他'

    def classify_batch(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """批量分类文章"""
        classified = {
            '固收类': [],
            '权益类': [],
            '宏观类': [],
            '其他': []
        }

        for article in articles:
            article_type = self.classify(
                title=article.get('title', ''),
                institution=article.get('institution', ''),
                content=article.get('content', '')[:500] if article.get('content') else '',
                content_type=article.get('content_type', '')
            )
            article['article_type'] = article_type
            classified[article_type].append(article)

        return classified