# 债券市场观点自动化分析系统

一个基于AI的债券市场研究报告自动化分析系统，
能够自动获取、分析各机构发布的债券市场观点，并生成综合分析报告。

## 功能特点

- 🔍 **自动获取**：支持从微信公众号和其他网站自动获取研究报告
- 🤖 **AI分析**：使用DeepSeek API深度分析文章内容
- 📊 **多维度评估**：从基本面、资金面、政策面等多个维度分析市场
- 📈 **收益率预测**：综合各机构观点生成收益率预测
- 📝 **报告生成**：自动生成Excel和文本格式的分析报告

## 项目结构
bond-market-analyzer/
├── config/
│   ├── __init__.py ✓
│   └── settings.py ✓
├── crawler/
│   ├── __init__.py ✓
│   ├── base_crawler.py ✓
│   ├── wechat_crawler.py ✓
│   └── jina_crawler.py ✓
├── analyzer/
│   ├── __init__.py ✓
│   ├── article_analyzer.py ✓
│   ├── market_analyzer.py ✓
│   └── prompts.py ✓
├── api/
│   ├── __init__.py 
│   └── deepseek_client.py ✓
├── report/
│   ├── __init__.py ✓
│   ├── excel_generator.py ✓
│   └── text_generator.py ✓
├── utils/
│   ├── __init__.py 
│   ├── file_handler.py ✓
│   ├── logger.py ✓
│   └── data_processor.py
