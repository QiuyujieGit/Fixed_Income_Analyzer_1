import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from config.setting import OUTPUT_DIR


class ExcelGenerator:
    """Excel报告生成器"""

    def __init__(self):
        self.output_dir = OUTPUT_DIR

    def create_summary_dataframe(self, analyses: List[Dict[str, Any]]) -> pd.DataFrame:
        """创建分析汇总DataFrame（供Main.py调用）"""
        table_data = []
        
        for i, analysis in enumerate(analyses, 1):
            forecast_10y = analysis.get('10Y国债收益率预测', {})
            forecast_5y = analysis.get('5Y国债收益率预测', {})
            score_details = analysis.get('评分细项', {})
            
            if not isinstance(forecast_10y, dict):
                forecast_10y = {}
            if not isinstance(forecast_5y, dict):
                forecast_5y = {}
            if not isinstance(score_details, dict):
                score_details = {}
            
            row = {
                '序号': i,
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
            table_data.append(row)
        
        df = pd.DataFrame(table_data)
        
        # 按重要性评分排序
        if not df.empty and '重要性评分' in df.columns:
            df = df.sort_values('重要性评分', ascending=False).reset_index(drop=True)
            df['序号'] = range(1, len(df) + 1)  # 重新编号
        
        return df

    def generate(self, analyses: List[Dict[str, Any]], timestamp: str) -> str:
        """生成Excel报告

        Args:
            analyses: 分析结果列表
            timestamp: 时间戳

        Returns:
            str: 生成的Excel文件路径
        """
        # 创建数据框架
        df = self.create_summary_dataframe(analyses)  # 使用统一的方法

        # 生成文件路径
        filename = f'债券市场分析结果_{timestamp}.xlsx'
        filepath = os.path.join(self.output_dir, filename)

        # 保存并格式化Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # 主分析表
            df.to_excel(writer, sheet_name='分析结果', index=False)

            # 添加汇总统计表
            summary_df = self._create_summary_sheet(analyses)
            summary_df.to_excel(writer, sheet_name='汇总统计', index=True)

            # 添加收益率预测表
            yield_df = self._create_yield_forecast_sheet(analyses)
            yield_df.to_excel(writer, sheet_name='收益率预测', index=False)

        # 格式化Excel
        self._format_excel(filepath)

        return filepath

    def _create_summary_sheet(self, analyses: List[Dict[str, Any]]) -> pd.DataFrame:
        """创建汇总统计表"""
        # 统计各维度观点数量
        dimension_counts = {
            '基本面及通胀': 0,
            '资金面': 0,
            '货币及财政政策': 0,
            '机构行为': 0,
            '海外及其他': 0
        }

        # 统计文章类型
        article_types = {}

        # 统计机构分布
        institution_counts = {}

        # 收益率预测统计
        yield_predictions = {
            '10Y上行': 0,
            '10Y下行': 0,
            '10Y震荡': 0,
            '5Y上行': 0,
            '5Y下行': 0,
            '5Y震荡': 0
        }

        for analysis in analyses:
            # 统计维度
            for dim in dimension_counts:
                if analysis.get(dim) and len(str(analysis.get(dim))) > 10:
                    dimension_counts[dim] += 1

            # 统计文章类型
            for type_name in analysis.get('文章类型', []):
                article_types[type_name] = article_types.get(type_name, 0) + 1

            # 统计机构
            inst = analysis.get('机构', '未知')
            institution_counts[inst] = institution_counts.get(inst, 0) + 1

            # 统计收益率预测
            forecast_10y = analysis.get('10Y国债收益率预测', {})
            forecast_5y = analysis.get('5Y国债收益率预测', {})

            if isinstance(forecast_10y, dict):
                direction = forecast_10y.get('方向', '')
                if '上' in direction:
                    yield_predictions['10Y上行'] += 1
                elif '下' in direction:
                    yield_predictions['10Y下行'] += 1
                elif '震荡' in direction:
                    yield_predictions['10Y震荡'] += 1

            if isinstance(forecast_5y, dict):
                direction = forecast_5y.get('方向', '')
                if '上' in direction:
                    yield_predictions['5Y上行'] += 1
                elif '下' in direction:
                    yield_predictions['5Y下行'] += 1
                elif '震荡' in direction:
                    yield_predictions['5Y震荡'] += 1

        # 创建汇总数据
        summary_data = {
            '统计项': [],
            '数量': [],
            '占比': []
        }

        total_articles = len(analyses)

        # 添加总体统计
        summary_data['统计项'].append('文章总数')
        summary_data['数量'].append(total_articles)
        summary_data['占比'].append('100%')

        # 添加维度统计
        for dim, count in dimension_counts.items():
            summary_data['统计项'].append(f'{dim}观点')
            summary_data['数量'].append(count)
            summary_data['占比'].append(f'{count / total_articles * 100:.1f}%' if total_articles > 0 else '0%')

        # 添加收益率预测统计
        for pred, count in yield_predictions.items():
            summary_data['统计项'].append(f'{pred}预测')
            summary_data['数量'].append(count)
            summary_data['占比'].append(f'{count / total_articles * 100:.1f}%' if total_articles > 0 else '0%')

        return pd.DataFrame(summary_data)

    def _create_yield_forecast_sheet(self, analyses: List[Dict[str, Any]]) -> pd.DataFrame:
        """创建收益率预测汇总表"""
        yield_data = []

        for analysis in analyses:
            if analysis.get('重要性评分', 0) < 6:  # 只包含高质量分析
                continue

            forecast_10y = analysis.get('10Y国债收益率预测', {})
            forecast_5y = analysis.get('5Y国债收益率预测', {})

            if not isinstance(forecast_10y, dict):
                forecast_10y = {}
            if not isinstance(forecast_5y, dict):
                forecast_5y = {}

            # 只添加有明确预测的记录
            if (forecast_10y.get('区间') and forecast_10y.get('区间') != '文章未涉及') or \
                    (forecast_5y.get('区间') and forecast_5y.get('区间') != '文章未涉及'):
                yield_data.append({
                    '机构': analysis.get('机构', ''),
                    '发布日期': analysis.get('日期', ''),
                    '10Y方向': forecast_10y.get('方向', ''),
                    '10Y区间': forecast_10y.get('区间', ''),
                    '10Y概率': forecast_10y.get('概率', ''),
                    '10Y理由': forecast_10y.get('理由', ''),
                    '5Y方向': forecast_5y.get('方向', ''),
                    '5Y区间': forecast_5y.get('区间', ''),
                    '5Y概率': forecast_5y.get('概率', ''),
                    '5Y理由': forecast_5y.get('理由', ''),
                    '重要性评分': analysis.get('重要性评分', 0)
                })

        df = pd.DataFrame(yield_data)
        if not df.empty:
            df = df.sort_values('重要性评分', ascending=False)

        return df

    def _format_excel(self, filepath: str):
        """格式化Excel文件"""
        try:
            workbook = load_workbook(filepath)

            # 格式化主分析表
            if '分析结果' in workbook.sheetnames:
                ws = workbook['分析结果']
                self._format_analysis_sheet(ws)

            # 格式化汇总统计表
            if '汇总统计' in workbook.sheetnames:
                ws = workbook['汇总统计']
                self._format_summary_sheet(ws)

            # 格式化收益率预测表
            if '收益率预测' in workbook.sheetnames:
                ws = workbook['收益率预测']
                self._format_yield_sheet(ws)

            workbook.save(filepath)

        except Exception as e:
            print(f"格式化Excel时出错: {e}")

    def _format_analysis_sheet(self, ws):
        """格式化分析结果表"""
        # 设置标题行格式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # 设置边框
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # 应用标题行格式
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

        # 设置行高和列宽
        ws.row_dimensions[1].height = 30

        # 设置列宽（更新以包含新增的列）
        column_widths = {
            'A': 8,  # 序号
            'B': 15,  # 机构
            'C': 12,  # 发布日期
            'D': 30,  # 文章链接
            'E': 20,  # 文章类型
            'F': 50,  # 基本面及通胀
            'G': 50,  # 资金面
            'H': 50,  # 货币及财政政策
            'I': 50,  # 机构行为
            'J': 50,  # 海外及其他
            'K': 40,  # 整体观点
            'L': 40,  # 投资策略
            'M': 12,  # 10Y方向
            'N': 15,  # 10Y区间
            'O': 10,  # 10Y概率
            'P': 12,  # 5Y方向
            'Q': 15,  # 5Y区间
            'R': 10,  # 5Y概率
            'S': 12,  # 重要性评分
            'T': 12,  # 数据支撑分
            'U': 12,  # 逻辑完整分
            'V': 12,  # 策略价值分
            'W': 12,  # 观点独特分
            'X': 12,  # 市场影响分
            'Y': 30,  # 评分理由
            'Z': 10,  # 阅读量
        }

        for col, width in column_widths.items():
            if col in ws.column_dimensions:
                ws.column_dimensions[col].width = width

        # 设置数据区域格式
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                cell.border = thin_border

                # 根据评分设置颜色
                if cell.column == 19:  # 重要性评分列
                    try:
                        score = float(cell.value)
                        if score >= 8:
                            cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                        elif score >= 6:
                            cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                        else:
                            cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                    except:
                        pass

        # 冻结首行
        ws.freeze_panes = 'A2'

    def _format_summary_sheet(self, ws):
        """格式化汇总统计表"""
        # 设置标题行格式
        header_font = Font(bold=True)
        header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

        # 应用格式
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        # 设置列宽
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15

        # 设置数据格式
        for row in ws.iter_rows(min_row=2):
            row[0].alignment = Alignment(horizontal="left")
            row[1].alignment = Alignment(horizontal="center")
            row[2].alignment = Alignment(horizontal="center")

    def _format_yield_sheet(self, ws):
        """格式化收益率预测表"""
        # 设置标题行格式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

        # 应用标题行格式
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", wrap_text=True)

        # 设置列宽
        column_widths = {
            'A': 15,  # 机构
            'B': 12,  # 发布日期
            'C': 10,  # 10Y方向
            'D': 15,  # 10Y区间
            'E': 10,  # 10Y概率
            'F': 30,  # 10Y理由
            'G': 10,  # 5Y方向
            'H': 15,  # 5Y区间
            'I': 10,  # 5Y概率
            'J': 30,  # 5Y理由
            'K': 12,  # 重要性评分
        }

        for col, width in column_widths.items():
            if col in ws.column_dimensions:
                ws.column_dimensions[col].width = width

        # 设置行高
        ws.row_dimensions[1].height = 25

        # 冻结首行
        ws.freeze_panes = 'A2'
