"""文件处理工具 - 增强版"""
import os
import hashlib
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Optional
from config.setting import INPUT_DIR, CACHE_DIR


class FileHandler:
    """文件处理器"""

    def __init__(self):
        """初始化，设置文章分类关键词"""
        # 文章分类关键词
        self.bond_keywords = ['债', '利率', '信用', '固收', '货币', '央行', '流动性',
                             'MLF', 'LPR', '国债', '城投', '地产债', '金融债', '企业债',
                             '收益率', '可转债','转债','久期', '曲线', '资金面', '债市','利差','信用利差']

        self.equity_keywords = ['股', '权益', 'A股', '港股', '美股', '板块', '行业',
                               '个股', '涨跌', '估值', '市值', '创业板', '科创板',
                               '主板', '北交所', '沪深', '恒生', '纳斯达克']

        self.macro_keywords = ['宏观', '经济', 'GDP', 'CPI', 'PPI', 'PMI', '通胀',
                              '就业', '消费', '投资', '进出口', '贸易', '财政']

    @staticmethod
    def read_excel_links(file_name: str) -> Tuple[List[str], List[str], List[str], List[str]]:
        """从Excel读取链接"""
        file_path = os.path.join(INPUT_DIR, file_name)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        df = pd.read_excel(file_path)

        links = df['链接'].dropna().tolist()
        institutions = df['撰写机构'].tolist() if '撰写机构' in df.columns else [''] * len(links)
        dates = df['发布日期'].tolist() if '发布日期' in df.columns else [''] * len(links)
        contents = df['文章内容'].tolist() if '文章内容' in df.columns else [None] * len(links)

        return links, institutions, dates, contents

    def get_cache_path(self, url: str, institution: str, date: str, title: str = "",
                      article_type: Optional[str] = None) -> str:
        """获取缓存文件路径 - 按日期和类型组织"""
        # 创建日期文件夹
        date_folder = datetime.now().strftime('%Y%m%d')

        # 如果没有指定文章类型，则自动分类
        if not article_type:
            article_type = self._classify_article(title, institution)

        # 创建类型文件夹
        type_folder = article_type

        # 创建完整的缓存目录路径
        cache_dir = os.path.join(CACHE_DIR, date_folder, type_folder)
        os.makedirs(cache_dir, exist_ok=True)

        # 生成文件名
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        date_str = str(date).replace('/', '-').replace(' ', '_')[:10] if date else "未知日期"
        title_clean = self._sanitize_filename(title) if title else "未知标题"

        filename = f"{institution}_{date_str}_{title_clean}_{url_hash}.txt"
        return os.path.join(cache_dir, filename)

    def _classify_article(self, title: str, institution: str) -> str:
        """根据标题和机构分类文章"""
        # 合并标题和机构名进行分析
        text = f"{title} {institution}".lower() if title else institution.lower()

        # 计算各类别的关键词匹配数
        bond_count = sum(1 for keyword in self.bond_keywords if keyword.lower() in text)
        equity_count = sum(1 for keyword in self.equity_keywords if keyword.lower() in text)
        macro_count = sum(1 for keyword in self.macro_keywords if keyword.lower() in text)

        # 根据匹配数判断类型
        if bond_count > equity_count and bond_count > macro_count:
            return "固收类"
        elif equity_count > bond_count and equity_count > macro_count:
            return "权益类"
        elif macro_count > 0:
            return "宏观类"
        else:
            return "其他"

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """清理文件名"""
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        if len(filename) > 100:
            filename = filename[:100]
        return filename.strip()

    def check_cache(self, url: str, date_folder: Optional[str] = None) -> str:
        """检查缓存是否存在 - 支持按日期查找"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]

        # 如果指定了日期文件夹，只在该文件夹中查找
        if date_folder:
            search_path = os.path.join(CACHE_DIR, date_folder)
        else:
            search_path = CACHE_DIR

        if os.path.exists(search_path):
            # 递归搜索所有子目录
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if url_hash in file:
                        cache_file = os.path.join(root, file)
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            return f.read()

        return ""

    @staticmethod
    def save_cache(content: str, cache_path: str):
        """保存缓存"""
        # 确保目录存在
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def get_cache_statistics(self, date_folder: Optional[str] = None) -> dict:
        """获取缓存统计信息"""
        stats = {
            '固收类': 0,
            '权益类': 0,
            '宏观类': 0,
            '其他': 0,
            '总计': 0
        }

        # 确定搜索路径
        if date_folder:
            search_path = os.path.join(CACHE_DIR, date_folder)
        else:
            search_path = CACHE_DIR

        if not os.path.exists(search_path):
            return stats

        # 统计各类型文件数量
        for type_folder in ['固收类', '权益类', '宏观类', '其他']:
            type_path = os.path.join(search_path, type_folder) if date_folder else search_path
            if os.path.exists(type_path):
                if os.path.isdir(type_path):
                    stats[type_folder] = len([f for f in os.listdir(type_path) if f.endswith('.txt')])

        stats['总计'] = sum(stats[k] for k in ['固收类', '权益类', '宏观类', '其他'])

        return stats

    def clean_old_cache(self, days_to_keep: int = 7):
        """清理旧的缓存文件"""
        if not os.path.exists(CACHE_DIR):
            return

        current_date = datetime.now()

        for folder in os.listdir(CACHE_DIR):
            folder_path = os.path.join(CACHE_DIR, folder)

            # 检查是否是日期文件夹（格式：YYYYMMDD）
            if len(folder) == 8 and folder.isdigit():
                try:
                    folder_date = datetime.strptime(folder, '%Y%m%d')
                    # 如果文件夹超过保留天数，删除
                    if (current_date - folder_date).days > days_to_keep:
                        import shutil
                        shutil.rmtree(folder_path)
                        print(f"已清理缓存文件夹: {folder}")
                except ValueError:
                    continue
