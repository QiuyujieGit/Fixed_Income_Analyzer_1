"""DeepSeek API客户端"""
import time
import logging
from openai import OpenAI
from config.setting import DEEPSEEK_API_KEY, DEEPSEEK_API_URL


class DeepSeekClient:
    """DeepSeek API客户端"""

    def __init__(self):
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_API_URL
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def chat(self, prompt: str, max_retries: int = 3) -> str:
        """调用聊天API"""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"API调用尝试 {attempt + 1}/{max_retries}")

                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的债券市场分析师，擅长分析利率债市场走势和收益率预测。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    stream=False,
                    temperature=0.7,
                    max_tokens=8000
                )

                result = response.choices[0].message.content
                self.logger.info("API调用成功")
                return result

            except Exception as e:
                self.logger.error(f"API调用失败 (尝试 {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    self.logger.error("API调用最终失败")
                    return ""
                else:
                    time.sleep(3)
