# 债券市场观点自动化分析系统

一个基于AI的债券市场研究报告自动化分析系统，
能够自动获取、分析各机构发布的债券市场观点，并生成综合分析报告。

## 更新-0530
- **Main主程序更新**：更新主程序的调用方式和运行日志内容
- **更新Data Processor**: 在Utils中，更新了Data_Processor的功能模块
- **更新定向爬取**：更新定向爬取33个公众号的功能
- **更新每日爬取**：更新每日爬取的功能
- **更新文件分类器**：更新了爬取的文件的分类，按照权益、宏观、固收进行分类
- **增加用户选择器**：让用户自行选择需要分析的对象，避免权益类的文章也纳入分析维度

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
- 1.简化Main.PY主程序代码的结构，把各种类和功能代码拆出去，减少主程序代码的冗余
- 2.继续Debug，代码的完整性及整合
- 3.优化文字报告的赎出
