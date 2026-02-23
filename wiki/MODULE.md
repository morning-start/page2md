# page2md 模块文档

## 模块概览

| 模块 | 路径 | 说明 |
|------|------|------|
| crawler | `src/page2md/crawler.py` | 爬虫核心 |
| models | `src/page2md/models.py` | 数据类型 |
| utils | `src/page2md/utils.py` | 工具函数 |
| config | `src/page2md/config.py` | 配置管理 |

## crawler 模块

### 核心类

#### HtmlToMarkdown

主要爬虫类，负责网页的爬取和转换。

```python
class HtmlToMarkdown:
    def __init__(
        self,
        urls: Union[str, List[str]],  # URL列表
        timeout: int = 30,            # 超时时间
        wait_until: str = "networkidle", # 等待策略
        headless: bool = True,         # 无头模式
        max_workers: int = 5,          # 并行数
        save_callback: Callable = None,# 保存回调
        content_selectors: List[str] = None,  # 内容选择器
        title_selectors: List[str] = None,    # 标题选择器
        retry_times: int = 3,         # 重试次数
        incremental_crawl: bool = False, # 增量爬取
        skip_existing: bool = False,  # 跳过已存在
    )
```

#### 关键方法

| 方法 | 说明 |
|------|------|
| `fetch()` | 顺序爬取所有 URL |
| `fetch_parallel()` | 并行爬取所有 URL |
| `get_results()` | 获取所有爬取结果 |
| `export_results()` | 导出结果为 JSON/Markdown/CSV |
| `save_to_dir()` | 保存到目录 |

### 便捷函数

```python
def crawl_urls(
    urls: List[str],
    output_dir: str = None,
    headless: bool = True,
    max_workers: int = 5,
    timeout: int = 30,
) -> Dict[str, str]:
    """快速爬取 URL 列表"""
```

## models 模块

### 数据类型

| 类名 | 说明 |
|------|------|
| `CrawlStatus` | 爬取状态枚举 (PENDING, RUNNING, SUCCESS, FAILED, SKIPPED) |
| `PageMetadata` | 页面元数据 |
| `CrawlResult` | 爬取结果 |
| `CrawlStats` | 爬取统计信息 |
| `SidebarItem` | 侧边栏项 |
| `SaveOptions` | 保存选项 |
| `ProgressInfo` | 进度信息 |

### CrawlStats 属性

```python
@dataclass
class CrawlStats:
    total: int = 0       # 总数
    success: int = 0     # 成功数
    failed: int = 0     # 失败数
    skipped: int = 0     # 跳过数
    
    @property
    def duration(self) -> float:  # 总耗时
    
    @property
    def success_rate(self) -> float:  # 成功率
```

## utils 模块

### 工具函数分类

#### URL 处理

| 函数 | 说明 |
|------|------|
| `url_to_filename()` | URL 转文件名 |
| `normalize_url()` | 标准化 URL |
| `get_url_hash()` | URL 哈希 |
| `filter_urls()` | 过滤 URL |
| `deduplicate_urls()` | URL 去重 |
| `group_urls_by_domain()` | 按域名分组 |

#### 内容处理

| 函数 | 说明 |
|------|------|
| `extract_content()` | 提取页面主要内容 |
| `extract_title()` | 提取页面标题 |
| `fix_image_paths()` | 修复图片路径 |
| `fix_links()` | 修复链接 |
| `clean_markdown()` | 清理 Markdown |

#### 侧边栏处理

| 函数 | 说明 |
|------|------|
| `flatten_siderbar()` | 展平侧边栏字典为 URL 列表 |
| `collect_urls()` | 收集 URL |

#### 回调函数

| 函数 | 说明 |
|------|------|
| `make_save_callback()` | 创建保存回调 |
| `make_progress_callback()` | 创建进度回调 |

#### 状态管理

| 函数 | 说明 |
|------|------|
| `load_crawled_urls()` | 加载已爬取 URL |
| `save_crawled_urls()` | 保存已爬取 URL |
| `build_url_index()` | 构建 URL 索引 |
| `load_url_index()` | 加载 URL 索引 |

## config 模块

### 默认配置

```python
DEFAULT_CONFIG = {
    "timeout": 30,
    "wait_until": "networkidle",
    "headless": True,
    "max_workers": 5,
    "retry_times": 3,
    "extract_title": True,
    "browser_args": [],
}
```

### 配置管理函数

- `load_config()`: 加载配置
- `save_config()`: 保存配置
- `merge_config()`: 合并配置
- `create_config()`: 创建配置
- `validate_config()`: 验证配置
