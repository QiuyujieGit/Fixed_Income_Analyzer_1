"""微信公众号文章爬虫"""
import json
import os
import re
import time
import requests
from lxml import etree
from .base_crawler import BaseCrawler


class WechatCrawler(BaseCrawler):
    """微信文章爬虫"""

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.token = None
        self.cookie = None
        self.load_credentials()

    def load_credentials(self):
        """加载保存的凭证"""
        cred_file = 'wechat_credentials.json'
        if os.path.exists(cred_file):
            with open(cred_file, 'r') as f:
                creds = json.load(f)
                self.token = creds.get('token')
                self.cookie = creds.get('cookie')
                if self.cookie:
                    self.session.headers.update({'Cookie': self.cookie})

    def save_credentials(self):
        """保存凭证"""
        with open('wechat_credentials.json', 'w') as f:
            json.dump({
                'token': self.token,
                'cookie': self.cookie
            }, f)

    def login(self):
        """登录微信公众平台"""
        try:
            from DrissionPage import ChromiumPage

            self.logger.info("正在打开微信公众平台登录页面...")
            browser = ChromiumPage()
            browser.get('https://mp.weixin.qq.com/')
            browser.set.window.max()

            while 'token' not in browser.url:
                time.sleep(1)

            self.token = re.search(r'token=(\d+)', browser.url).group(1)

            cookies = browser.cookies()
            cookie_str = ''
            for c in cookies:
                cookie_str += f"{c['name']}={c['value']}; "
            self.cookie = cookie_str.strip()

            self.session.headers.update({'Cookie': self.cookie})
            self.save_credentials()

            browser.close()
            self.logger.info("登录成功！")
            return True

        except Exception as e:
            self.logger.error(f"登录失败: {e}")
            return False

    def fetch_content(self, url: str) -> tuple[str, str]:
        """获取微信文章内容"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': self.cookie if self.cookie else ''
            }

            response = self.session.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'

            tree = etree.HTML(response.text)

            # 获取标题
            title = ""
            title_selectors = [
                '//h1[@class="rich_media_title"]/text()',
                '//h2[@class="rich_media_title"]/text()',
                '//title/text()'
            ]

            for selector in title_selectors:
                title_elements = tree.xpath(selector)
                if title_elements:
                    title = title_elements[0].strip()
                    break

            # 获取内容
            content_selectors = [
                '//div[@id="js_content"]',
                '//div[@class="rich_media_content"]',
                '//div[@class="weui-msg__text-area"]'
            ]

            content = ""
            for selector in content_selectors:
                elements = tree.xpath(selector)
                if elements:
                    content = etree.tostring(elements[0], encoding='unicode', method='text')
                    content = re.sub(r'\s+', ' ', content).strip()
                    break

            # 检查是否需要登录
            if not content or len(content) < 100:
                if "环境异常" in response.text or "验证" in response.text:
                    self.logger.warning("检测到需要验证，尝试登录...")
                    if not self.token:
                        self.login()
                    return "", ""

            return content, title

        except Exception as e:
            self.logger.error(f"获取文章内容失败: {e}")
            return "", ""

    def is_valid_url(self, url: str) -> bool:
        """检查是否是微信文章URL"""
        return "mp.weixin.qq.com" in url
