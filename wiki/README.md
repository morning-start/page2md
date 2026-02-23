# page2md - HTML 转 Markdown 工具

## 项目概述

page2md 是一个 Python 库，专门用于将网页（HTML）转换为 Markdown 格式。它使用 DrissionPage 库控制浏览器，支持单页爬取和批量并行爬取。

## 核心功能

- **HTML 转 Markdown**: 将网页内容转换为 Markdown 格式
- **批量爬取**: 支持多线程并行爬取多个页面
- **增量爬取**: 支持增量爬取，保存已爬取状态
- **灵活配置**: 支持自定义选择器、超时设置、重试机制等

## 快速开始

```python
from html2md import HtmlToMarkdown, crawl_urls

# 方式一：使用类
with HtmlToMarkdown(
    urls=["https://example.com"],
    headless=True,
    max_workers=5,
) as crawler:
    results = crawler.fetch_parallel()

# 方式二：使用便捷函数
results = crawl_urls(
    urls=["https://example.com"],
    output_dir="./output",
)

# 方式三：使用 save_callback 自定义保存
from html2md import make_save_callback, url_to_filename

output_dir = Path("./output")
save_callback = make_save_callback(
    output_dir,
    filename_func=lambda url: url_to_filename(url, domain="https://example.com"),
    domain="https://example.com",
)

with HtmlToMarkdown(
    urls=["https://example.com/docs/intro"],
    headless=True,
    save_callback=save_callback,
) as crawler:
    results = crawler.fetch_parallel()
```

## 技术栈

- **Python**: >=3.12
- **DrissionPage**: 浏览器控制
- **markdownify**: HTML 转 Markdown
- **loguru**: 日志
- **tqdm**: 进度条
