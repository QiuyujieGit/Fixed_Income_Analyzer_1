# utils/file_handler.py
"""文件处理工具 - 简化版"""
import os
import hashlib
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Optional
from config.setting import INPUT_DIR, CACHE_DIR


class FileHandler:
    """文件处理器 - 只负责文件操作"""
    
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
    
    @staticmethod
    def get_cache_path(url: str, institution: str, date: str, title: str = "",
                      article_type: str = "其他") -> str:
        """获取缓存文件路径 - 按日期和类型组织"""
        # 创建日期文件夹
        date_folder = datetime.now().strftime('%Y%m%d')
        
        # 创建完整的缓存目录路径
        cache_dir = os.path.join(CACHE_DIR, date_folder, article_type)
        os.makedirs(cache_dir, exist_ok=True)
        
        # 生成文件名
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        date_str = str(date).replace('/', '-').replace(' ', '_')[:10] if date else "未知日期"
        title_clean = FileHandler._sanitize_filename(title) if title else "未知标题"
        institution_clean = FileHandler._sanitize_filename(institution) if institution else "未知机构"
        
        filename = f"{institution_clean}_{date_str}_{title_clean}_{url_hash}.txt"
        return os.path.join(cache_dir, filename)
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """清理文件名"""
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        if len(filename) > 50:
            filename = filename[:50]
        return filename.strip()
    
    @staticmethod
    def check_cache(url: str, date_folder: Optional[str] = None) -> str:
        """检查缓存是否存在"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        
        # 确定搜索路径
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
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def get_cache_statistics(date_folder: Optional[str] = None) -> dict:
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
        if date_folder:
            # 如果指定了日期，直接查看该日期下的分类文件夹
            for type_folder in ['固收类', '权益类', '宏观类', '其他']:
                type_path = os.path.join(search_path, type_folder)
                if os.path.exists(type_path) and os.path.isdir(type_path):
                    stats[type_folder] = len([f for f in os.listdir(type_path) if f.endswith('.txt')])
        else:
            # 遍历所有日期文件夹
            for date_dir in os.listdir(search_path):
                date_path = os.path.join(search_path, date_dir)
                if os.path.isdir(date_path) and date_dir.isdigit() and len(date_dir) == 8:
                    for type_folder in ['固收类', '权益类', '宏观类', '其他']:
                        type_path = os.path.join(date_path, type_folder)
                        if os.path.exists(type_path) and os.path.isdir(type_path):
                            stats[type_folder] += len([f for f in os.listdir(type_path) if f.endswith('.txt')])
        
        stats['总计'] = sum(stats[k] for k in ['固收类', '权益类', '宏观类', '其他'])
        
        return stats
    
    @staticmethod
    def clean_old_cache(days_to_keep: int = 7):
        """清理旧的缓存文件"""
        if not os.path.exists(CACHE_DIR):
            return
        
        current_date = datetime.now()
        cleaned_count = 0
        
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
                        cleaned_count += 1
                        print(f"已清理缓存文件夹: {folder}")
                except ValueError:
                    continue
        
        if cleaned_count > 0:
            print(f"共清理 {cleaned_count} 个旧缓存文件夹")
