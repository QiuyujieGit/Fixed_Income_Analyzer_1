# 债券市场观点自动化分析系统

一个基于AI的债券市场研究报告自动化分析系统，
能够自动获取、分析各机构发布的债券市场观点，并生成综合分析报告。

## 更新-0529
- **Main主程序更新**：更新主程序的调用方式和运行日志内容
- **更新Data Processor**: 在Utils中，更新了Data_Processor的功能模块

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

## Todo List
- 1.按33个公众号进行滚动的爬取功能
- 2.增加每日定期进行爬取的功能
- 3.修改统计逻辑：
- 3.1 增加在Deepseek中对机构观点的（上行、下行、震荡）的聚合统计的功能点
- 3.2 增加对文章阅读量的统计字段，增加进入评分维度
- 3.3 修改文章的评分维度，使得文章的评分更加的公允，目前评分基本都是7分，说明评分维度没有很好的区分性
- 3.4 增加对机构观点，主要观点的NLP分析及提炼，即要知道主要的观点集中在哪里（注意需要考虑篇幅问题）
