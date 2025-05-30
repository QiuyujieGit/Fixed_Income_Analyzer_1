"""缓存管理器 - 统一管理所有缓存功能"""
import os
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict
from .file_handler import FileHandler
from .logger import setup_logger


class CacheManager:
    """缓存管理器 - 负责所有缓存相关功能"""

    def __init__(self):
        self.logger = setup_logger("CacheManager")
        self.file_handler = FileHandler()
        self.hash_cache_file = os.path.join('data', 'cache', 'article_hashes.json')
        self.article_hashes = self._load_article_hashes()
        self._article_classifier = None  # 延迟加载

    @property
    def article_classifier(self):
        """延迟加载文章分类器，避免循环导入"""
        if self._article_classifier is None:
            from utils.article_classifier import ArticleClassifier
            self._article_classifier = ArticleClassifier()
        return self._article_classifier

    def _load_article_hashes(self) -> dict:
        """加载已爬取文章的哈希值"""
        if os.path.exists(self.hash_cache_file):
            try:
                with open(self.hash_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_article_hashes(self):
        """保存文章哈希值"""
        os.makedirs(os.path.dirname(self.hash_cache_file), exist_ok=True)
        with open(self.hash_cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.article_hashes, f, ensure_ascii=False, indent=2)

    def _get_article_hash(self, title: str, institution: str, date: str) -> str:
        """生成文章唯一标识哈希"""
        content = f"{title}_{institution}_{date}"
        return hashlib.md5(content.encode()).hexdigest()

    def is_article_processed(self, title: str, institution: str, date: str) -> bool:
        """检查文章是否已处理"""
        article_hash = self._get_article_hash(title, institution, date)
        return article_hash in self.article_hashes

    def mark_article_processed(self, title: str, institution: str, date: str):
        """标记文章已处理"""
        article_hash = self._get_article_hash(title, institution, date)
        self.article_hashes[article_hash] = {
            'title': title,
            'institution': institution,
            'date': date,
            'processed_date': datetime.now().date().isoformat(),
            'processed_time': datetime.now().isoformat()
        }
        self._save_article_hashes()

    def get_cached_content(self, url: str) -> str:
        """获取缓存内容"""
        # 优先检查今天的缓存
        today_folder = datetime.now().strftime('%Y%m%d')
        content = self.file_handler.check_cache(url, today_folder)

        # 如果今天没有，检查所有缓存
        if not content:
            content = self.file_handler.check_cache(url)

        return content

    def save_article_cache(self, url: str, institution: str, date: str,
                           title: str, article_type: str, content: str):
        """保存文章缓存"""
        cache_path = self.file_handler.get_cache_path(
            url, institution, date, title, article_type
        )
        self.file_handler.save_cache(content, cache_path)
        self.logger.info(f"内容已缓存到: {article_type}/{os.path.basename(cache_path)}")

    def save_article_with_auto_classify(self, url: str, institution: str,
                                      date: str, title: str, content: str):
        """保存文章并自动分类"""
        # 使用分类器自动分类
        article_type = self.article_classifier.classify(
            title, institution, content[:500]
        )

        # 保存到缓存
        self.save_article_cache(url, institution, date, title, article_type, content)

    def get_today_articles_for_analysis(self) -> List[Dict]:
        """获取今天的缓存文章供分析"""
        today_folder = datetime.now().strftime('%Y%m%d')
        cache_path = os.path.join('data', 'cache', today_folder)

        if not os.path.exists(cache_path):
            self.logger.info("今天没有缓存文件夹")
            return []

        articles = []

        # 遍历所有类型文件夹
        for type_folder in ['固收类', '权益类', '宏观类', '其他']:
            type_path = os.path.join(cache_path, type_folder)
            if not os.path.exists(type_path):
                continue

            for file_name in os.listdir(type_path):
                if file_name.endswith('.txt'):
                    file_path = os.path.join(type_path, file_name)
                    article_info = self._parse_cached_article(file_path, type_folder)
                    if article_info:
                        articles.append(article_info)

        self.logger.info(f"找到 {len(articles)} 篇今日缓存文章")

        if not articles:
            return []

        # 显示文章并让用户选择
        return self._select_articles_for_analysis(articles)

    def _parse_cached_article(self, file_path: str, article_type: str) -> Dict:
        """解析缓存的文章文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            article_info = {
                'article_type': article_type
            }

            # 解析元数据
            lines = content.split('\n')
            metadata_found = False

            for i, line in enumerate(lines):
                if line.startswith('标题:'):
                    article_info['title'] = line.replace('标题:', '').strip()
                    metadata_found = True
                elif line.startswith('机构:'):
                    article_info['institution'] = line.replace('机构:', '').strip()
                elif line.startswith('日期:'):
                    article_info['date'] = line.replace('日期:', '').strip()
                elif line.startswith('链接:'):
                    article_info['link'] = line.replace('链接:', '').strip()
                    self.logger.debug(f"解析到链接: {article_info['link']}")
                elif line.startswith('阅读数:'):
                    try:
                        article_info['read_num'] = int(line.replace('阅读数:', '').strip() or '0')
                    except:
                        article_info['read_num'] = 0
                elif line.startswith('-' * 80):
                    # 找到分隔符，后面是正文
                    article_info['content'] = '\n'.join(lines[i + 1:]).strip()
                    break

            # 如果没有找到元数据，说明是旧格式或损坏的文件
            if not metadata_found:
                self.logger.warning(f"文件 {file_path} 缺少元数据，尝试从文件名恢复")
                # 从文件名尝试提取信息
                filename = os.path.basename(file_path)
                parts = filename.replace('.txt', '').split('_')
                if len(parts) >= 3:
                    article_info['institution'] = parts[0]
                    article_info['date'] = parts[1]
                    article_info['title'] = parts[2]
                article_info['content'] = content

            # 确保必要字段存在
            article_info.setdefault('title', '未知标题')
            article_info.setdefault('institution', '未知机构')
            article_info.setdefault('date', datetime.now().strftime('%Y-%m-%d'))
            article_info.setdefault('link', '')  # 如果没有链接，设为空字符串
            article_info.setdefault('content', '')

            # 调试信息
            self.logger.debug(f"解析文章: {article_info['title']}")
            self.logger.debug(f"  - 机构: {article_info['institution']}")
            self.logger.debug(f"  - 日期: {article_info['date']}")
            self.logger.debug(f"  - 链接: {article_info['link'] if article_info['link'] else '无链接'}")
            self.logger.debug(f"  - 内容长度: {len(article_info['content'])}")

            return article_info

        except Exception as e:
            self.logger.error(f"解析缓存文章失败 {file_path}: {e}")
            return None

    def _select_articles_for_analysis(self, articles: List[Dict]) -> List[Dict]:
        """让用户选择要分析的文章"""
        # 使用分类器分类
        classified_articles = self.article_classifier.classify_batch(articles)

        # 显示分类统计
        self._show_classification_stats(classified_articles)

        # 让用户选择分析模式
        analysis_mode = self._select_analysis_mode()

        # 根据选择返回筛选后的文章
        if analysis_mode == 'bond_only':
            filtered_articles = classified_articles.get('固收类', [])
            self.logger.info(f"仅分析固收类文章：{len(filtered_articles)}篇")
        elif analysis_mode == 'bond_macro':
            filtered_articles = (classified_articles.get('固收类', []) +
                               classified_articles.get('宏观类', []))
            self.logger.info(f"分析固收和宏观类文章：{len(filtered_articles)}篇")
        else:
            filtered_articles = articles
            self.logger.info(f"分析所有文章：{len(filtered_articles)}篇")

        return filtered_articles

    def _show_classification_stats(self, classified_articles: dict):
        """显示分类统计"""
        print("\n" + "=" * 60)
        print("文章分类统计")
        print("=" * 60)

        total = sum(len(articles) for articles in classified_articles.values())

        for category, articles in classified_articles.items():
            count = len(articles)
            percentage = (count / total * 100) if total > 0 else 0
            print(f"{category}: {count}篇 ({percentage:.1f}%)")

            if articles and count > 0:
                print(f"  示例文章:")
                for i, article in enumerate(articles[:3]):
                    title = article.get('title', '未知标题')
                    if len(title) > 50:
                        title = title[:50] + "..."
                    print(f"    {i + 1}. {title}")
                if count > 3:
                    print(f"    ... 还有{count - 3}篇")

        print("=" * 60)

    def _select_analysis_mode(self) -> str:
        """选择分析模式"""
        print("\n请选择分析模式:")
        print("1. 仅分析固收类文章（推荐）")
        print("2. 分析固收和宏观类文章")
        print("3. 分析所有文章")
        print("-" * 40)

        while True:
            choice = input("请选择 (1/2/3，默认1): ").strip() or "1"
            if choice == '1':
                return 'bond_only'
            elif choice == '2':
                return 'bond_macro'
            elif choice == '3':
                return 'all'
            else:
                print("无效选择，请重新输入")

    def show_today_statistics(self):
        """显示今日缓存统计"""
        today_folder = datetime.now().strftime('%Y%m%d')
        stats = self.file_handler.get_cache_statistics(today_folder)

        print("\n" + "=" * 60)
        print(f"今日缓存统计 ({today_folder})")
        print("=" * 60)
        for category, count in stats.items():
            if category != '总计':
                print(f"{category}: {count}篇")
        print("-" * 60)
        print(f"总计: {stats['总计']}篇")
        print("=" * 60)

    def clean_old_cache(self, days_to_keep: int = 7):
        """清理旧缓存"""
        self.file_handler.clean_old_cache(days_to_keep)
        self.logger.info(f"已清理{days_to_keep}天前的缓存文件")
