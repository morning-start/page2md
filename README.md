# page2md

将网页转换为 Markdown 的 Python 库。

## 安装

```bash
pip install page2md
```

## 快速开始

```python
from page2md import HtmlToMarkdown

# 单个 URL 转换
crawler = HtmlToMarkdown("https://example.com")
results = crawler.run()

for url, result in results.items():
    print(f"Title: {result.metadata.title}")
    print(f"Content:\n{result.content}")

# 批量转换
crawler = HtmlToMarkdown([
    "https://example.com/page1",
    "https://example.com/page2"
])
results = crawler.run()
```

## 功能特性

- 支持单个或批量 URL 转换
- 使用 DrissionPage 渲染动态网页
- 支持自定义 CSS 选择器
- 支持增量爬取
- 完善的错误处理和重试机制
- 进度回调支持

## 配置选项

详细配置请参考 [Config](.//config.py) 模块src/page2md。

## 许可证

MIT License
