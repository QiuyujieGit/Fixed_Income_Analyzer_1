"""文本报告生成器"""
import os
from datetime import datetime
from config.setting import OUTPUT_DIR


class TextGenerator:
    """文本报告生成器"""

    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.report_template = """债券市场观点总结报告
生成时间: {timestamp}
{separator}

{content}

{separator}
报告说明：
1. 本报告基于{article_count}篇机构研究报告自动生成
2. 收益率预测综合了多家机构观点，仅供参考
3. 详细分析数据请查看同期生成的Excel文件

{separator}
免责声明：
本报告由AI系统自动生成，所有观点来源于各机构公开发布的研究报告。
本报告不构成投资建议，投资者应独立判断，风险自担。
"""

    def generate(self, summary_content: str, timestamp: str, metadata: dict = None) -> str:
        """生成文本报告

        Args:
            summary_content: 总结内容
            timestamp: 时间戳
            metadata: 元数据（如文章数量等）

        Returns:
            str: 生成的文本文件路径
        """
        # 生成文件路径
        filename = f'债券市场观点报告_{timestamp}.txt'
        filepath = os.path.join(self.output_dir, filename)

        # 准备元数据
        if metadata is None:
            metadata = {}

        article_count = metadata.get('article_count', '多')

        # 格式化报告
        report_content = self.report_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            separator='=' * 80,
            content=summary_content,
            article_count=article_count
        )

        # 保存报告
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)

        # 同时生成Markdown版本
        self._generate_markdown_version(summary_content, timestamp, metadata)

        return filepath

    def _generate_markdown_version(self, summary_content: str, timestamp: str, metadata: dict):
        """生成Markdown版本的报告"""
        filename = f'债券市场观点报告_{timestamp}.md'
        filepath = os.path.join(self.output_dir, filename)

        markdown_content = f"""# 债券市场观点总结报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 市场观点总结

{self._convert_to_markdown(summary_content)}

---

## 数据来源

- 分析文章数量：{metadata.get('article_count', '多')}篇
- 涵盖机构：{', '.join(metadata.get('institutions', ['多家机构']))}
- 数据时间范围：{metadata.get('date_range', '最近一周')}

---

## 重要提示

1. 本报告基于公开市场研究报告自动生成
2. 所有预测和建议仅供参考，不构成投资建议
3. 市场有风险，投资需谨慎

---

*本报告由债券市场分析系统自动生成*
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

    def _convert_to_markdown(self, content: str) -> str:
        """将普通文本转换为Markdown格式"""
        lines = content.split('\n')
        markdown_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                markdown_lines.append('')
                continue

            # 识别编号列表
            if line[0:2] in ['1）', '2）', '3）', '4）', '5）', '6）']:
                line = line.replace('）', '. ', 1)
                markdown_lines.append(f"{line}")
            # 识别要点
            elif line.startswith('策略建议') or line.startswith('风险提示'):
                markdown_lines.append(f"\n### {line}")
            else:
                markdown_lines.append(line)

        return '\n'.join(markdown_lines)

    def generate_daily_digest(self, analyses: list, date: str) -> str:
        """生成每日观点摘要"""
        filename = f'债券市场日报_{date}.txt'
        filepath = os.path.join(self.output_dir, 'daily_reports', filename)

        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # 生成摘要内容
        digest_content = self._create_daily_digest(analyses, date)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(digest_content)

        return filepath

    def _create_daily_digest(self, analyses: list, date: str) -> str:
        """创建每日摘要内容"""
        # 按机构分组
        by_institution = {}
        for analysis in analyses:
            inst = analysis.get('机构', '未知')
            if inst not in by_institution:
                by_institution[inst] = []
            by_institution[inst].append(analysis)

        # 生成摘要
        lines = [
            f"债券市场观点日报 - {date}",
            "=" * 50,
            "",
            f"今日共收录{len(analyses)}篇研究报告，涉及{len(by_institution)}家机构",
            "",
            "【主要观点】",
            ""
        ]

        # 添加各机构观点
        for inst, inst_analyses in by_institution.items():
            lines.append(f"◆ {inst}")
            for analysis in inst_analyses:
                score = analysis.get('重要性评分', 0)
                if score >= 7:  # 只包含高质量观点
                    lines.append(f"  - {analysis.get('整体观点', '')[:100]}...")
            lines.append("")

        # 添加收益率预测汇总
        lines.extend([
            "【收益率预测】",
            self._summarize_yield_predictions(analyses),
            "",
            "【策略建议】",
            self._summarize_strategies(analyses),
            "",
            "-" * 50,
            "详细内容请查看完整分析报告"
        ])

        return '\n'.join(lines)

    def _summarize_yield_predictions(self, analyses: list) -> str:
        """汇总收益率预测"""
        predictions_10y = {'上行': 0, '下行': 0, '震荡': 0}
        predictions_5y = {'上行': 0, '下行': 0, '震荡': 0}

        for analysis in analyses:
            forecast_10y = analysis.get('10Y国债收益率预测', {})
            if isinstance(forecast_10y, dict):
                direction = forecast_10y.get('方向', '')
                if '上' in direction:
                    predictions_10y['上行'] += 1
                elif '下' in direction:
                    predictions_10y['下行'] += 1
                elif '震荡' in direction:
                    predictions_10y['震荡'] += 1

        # 生成预测文本
        total = sum(predictions_10y.values())
        if total > 0:
            main_view = max(predictions_10y.items(), key=lambda x: x[1])
            return f"10Y国债：{main_view[1]}家机构预测{main_view[0]}（占比{main_view[1] / total * 100:.0f}%）"

        return "暂无明确的收益率预测"

    def _summarize_strategies(self, analyses: list) -> str:
        """汇总投资策略"""
        strategies = []

        for analysis in analyses:
            if analysis.get('重要性评分', 0) >= 7:
                strategy = analysis.get('投资策略', '')
                if strategy and len(strategy) > 20:
                    strategies.append(f"- {analysis.get('机构')}：{strategy[:80]}...")

        if strategies:
            return '\n'.join(strategies[:3])  # 只取前3个

        return "暂无具体策略建议"