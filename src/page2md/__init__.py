"""
html2md - HTML to Markdown Converter

一个将网页转换为 Markdown 的 Python 库。
"""

from .config import (
    DEFAULT_CONFIG,
    ConfigManager,
    CrawlerConfig,
    create_config,
    load_config,
    merge_config,
    save_config,
    validate_config,
)
from .crawler import HtmlToMarkdown, crawl_urls
from .models import (
    CrawlResult,
    CrawlStats,
    CrawlStatus,
    PageMetadata,
    ProgressInfo,
    SaveOptions,
    SidebarItem,
)
from .utils import (
    batch_url_to_filename,
    build_url_index,
    clean_markdown,
    deduplicate_urls,
    estimate_crawl_time,
    extract_content,
    extract_title,
    filter_urls,
    fix_image_paths,
    fix_links,
    flatten_siderbar,
    get_url_hash,
    group_urls_by_domain,
    load_crawled_urls,
    load_url_index,
    make_progress_callback,
    make_save_callback,
    normalize_url,
    save_crawled_urls,
    url_to_filename,
)

__version__ = "1.0.0"
__all__ = [
    # 核心类
    "HtmlToMarkdown",
    "crawl_urls",
    # 数据类型
    "CrawlResult",
    "CrawlStats",
    "CrawlStatus",
    "PageMetadata",
    "ProgressInfo",
    "SaveOptions",
    "SidebarItem",
    # 工具函数
    "flatten_siderbar",
    "url_to_filename",
    "make_save_callback",
    "make_progress_callback",
    "extract_content",
    "extract_title",
    "fix_image_paths",
    "fix_links",
    "clean_markdown",
    "batch_url_to_filename",
    "group_urls_by_domain",
    "filter_urls",
    "deduplicate_urls",
    "normalize_url",
    "get_url_hash",
    "load_crawled_urls",
    "save_crawled_urls",
    "build_url_index",
    "load_url_index",
    "estimate_crawl_time",
    # 配置管理
    "CrawlerConfig",
    "DEFAULT_CONFIG",
    "load_config",
    "save_config",
    "merge_config",
    "create_config",
    "validate_config",
    "ConfigManager",
]
