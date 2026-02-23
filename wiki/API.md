# page2md API 文档

## 导入方式

```python
from html2md import (
    HtmlToMarkdown,
    crawl_urls,
    CrawlResult,
    CrawlStats,
    CrawlStatus,
    PageMetadata,
    ProgressInfo,
    SaveOptions,
    SidebarItem,
    flatten_siderbar,
    collect_urls,
    url_to_filename,
    make_save_callback,
    make_progress_callback,
    extract_content,
    extract_title,
    fix_image_paths,
    fix_links,
    clean_markdown,
    batch_url_to_filename,
    group_urls_by_domain,
    filter_urls,
    deduplicate_urls,
    normalize_url,
    get_url_hash,
    load_crawled_urls,
    save_crawled_urls,
    build_url_index,
    load_url_index,
    estimate_crawl_time,
    CrawlerConfig,
    DEFAULT_CONFIG,
    load_config,
    save_config,
    merge_config,
    create_config,
    validate_config,
    ConfigManager,
)
```

## 核心 API

### HtmlToMarkdown 类

```python
from html2md import HtmlToMarkdown

# 初始化
crawler = HtmlToMarkdown(
    urls=["https://example.com/page1", "https://example.com/page2"],
    timeout=30,              # 页面加载超时(秒)
    wait_until="networkidle", # 等待策略
    headless=True,           # 是否无头模式
    max_workers=5,           # 并行工作线程数
    retry_times=3,           # 重试次数
    extract_title=True,      # 是否提取标题
    incremental_crawl=False, # 是否增量爬取
    skip_existing=False,     # 是否跳过已存在的
)

# 爬取
results = crawler.fetch()              # 顺序爬取
results = crawler.fetch_parallel()     # 并行爬取

# 获取结果
all_results = crawler.get_results()    # 所有结果
success_results = crawler.get_successful()  # 成功结果
failed_results = crawler.get_failed()  # 失败结果

# 统计信息
stats = crawler.get_stats()            # 爬取统计
progress = crawler.get_progress()      # 进度信息

# 导出
crawler.export_results("output.json", format="json")
crawler.export_results("output.md", format="markdown")
crawler.export_results("output.csv", format="csv")

# 保存到目录
crawler.save_to_dir("./output")

# 关闭
crawler.close()

# 上下文管理
with HtmlToMarkdown(urls=["https://example.com"]) as crawler:
    results = crawler.fetch_parallel()
```

### crawl_urls 函数

```python
from html2md import crawl_urls

# 快速爬取
results = crawl_urls(
    urls=["https://example.com/page1", "https://example.com/page2"],
    output_dir="./output",   # 输出目录
    headless=True,           # 无头模式
    max_workers=5,          # 并行数
    timeout=30,             # 超时
)
# 返回: {url: markdown}
```

## 数据类型

### CrawlStatus 枚举

```python
from html2md import CrawlStatus

status = CrawlStatus.PENDING    # 等待中
status = CrawlStatus.RUNNING    # 运行中
status = CrawlStatus.SUCCESS    # 成功
status = CrawlStatus.FAILED     # 失败
status = CrawlStatus.SKIPPED    # 跳过
```

### PageMetadata

```python
from html2md import PageMetadata

metadata = PageMetadata(
    url="https://example.com",
    title="Page Title",
    status=CrawlStatus.SUCCESS,
)
```

属性:
- `duration`: 爬取耗时
- `is_success`: 是否成功

### CrawlResult

```python
from html2md import CrawlResult

result = CrawlResult(
    url="https://example.com",
    markdown="# Markdown content",
    metadata=metadata,
)
```

### CrawlStats

```python
from html2md import CrawlStats

stats = CrawlStats()
stats.total = 10
stats.success = 8
stats.failed = 2

print(stats.duration)      # 总耗时(秒)
print(stats.success_rate)  # 成功率(%)
print(stats.to_dict())     # 转为字典
```

### SidebarItem

```python
from html2md import SidebarItem

item = SidebarItem(
    title="Section",
    path="/docs/section",
    children=[],
)
```

### SaveOptions

```python
from html2md import SaveOptions

options = SaveOptions(
    output_dir="./output",
    filename_func=lambda url: "custom.md",
    domain="https://example.com",
    create_index=True,
    overwrite=True,
)
```

## 工具函数

### url_to_filename

```python
from html2md import url_to_filename

filename = url_to_filename(
    "https://example.com/docs/page.html",
    domain="https://example.com",
    suffix=".md",
    index_name="index",
)
# 结果: "docs/page.md"
```

### flatten_siderbar

```python
from html2md import flatten_siderbar

sidebar = {
    "Section 1": {
        "Page 1": "/docs/page1",
        "Page 2": "/docs/page2",
    }
}
urls = flatten_siderbar(sidebar, "https://example.com")
# 结果: [("Page 1", "https://example.com/docs/page1"), ...]
```

### make_save_callback

```python
from html2md import make_save_callback, url_to_filename

callback = make_save_callback(
    output_dir="./output",
    filename_func=lambda url: url_to_filename(url, domain="https://example.com"),
    domain="https://example.com",
)

# 作为 HtmlToMarkdown 的 save_callback 使用
crawler = HtmlToMarkdown(urls=urls, save_callback=callback)
```

### make_progress_callback

```python
from html2md import make_progress_callback

callback = make_progress_callback(
    total=100,
    desc="爬取进度",
    unit="page",
)

crawler.fetch_parallel(progress_callback=callback)
```

### fix_image_paths / fix_links

```python
from html2md import fix_image_paths, fix_links

markdown = fix_image_paths(markdown, base_url)
markdown = fix_links(markdown, base_url)
```

### clean_markdown

```python
from html2md import clean_markdown

markdown = clean_markdown(
    markdown,
    remove_selectors=["nav", "footer"],
    strip_empty_lines=True,
    normalize_whitespace=True,
)
```

### filter_urls / deduplicate_urls

```python
from html2md import filter_urls, deduplicate_urls

urls = filter_urls(
    urls,
    include=["docs"],    # 包含
    exclude=["admin"],   # 排除
)

urls = deduplicate_urls(urls, keep="first")
```

### estimate_crawl_time

```python
from html2md import estimate_crawl_time

time = estimate_crawl_time(
    url_count=100,
    avg_time_per_page=3.0,
    max_workers=5,
)
# 返回预估秒数
```

## 配置管理

### DEFAULT_CONFIG

```python
from html2md import DEFAULT_CONFIG

print(DEFAULT_CONFIG)
# {'timeout': 30, 'wait_until': 'networkidle', ...}
```

### load_config / save_config

```python
from html2md import load_config, save_config, merge_config

# 加载
config = load_config("config.json")

# 保存
save_config(config, "config.json")

# 合并
config = merge_config(DEFAULT_CONFIG, {"timeout": 60})
```
