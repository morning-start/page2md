"""工具函数模块"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

from tqdm import tqdm


def flatten_siderbar(
    sidebar_dict: Dict[str, Any],
    domain: str,
    base_path: str = "",
) -> List[tuple]:
    """
    递归展平侧边栏字典为 URL 列表。

    Args:
        sidebar_dict: 侧边栏字典，值为路径或嵌套字典
        domain: 域名
        base_path: 基础路径

    Returns:
        [(标题, URL), ...] 列表

    Example:
        >>> sidebar = {'section': {'page': '/docs/page.html'}}
        >>> flatten_siderbar(sidebar, 'https://example.com')
        [('page', 'https://example.com/docs/page.html')]
    """
    urls = []

    def process_section(section: Dict[str, Any], path_prefix: str = ""):
        for title, path in section.items():
            if isinstance(path, dict):
                process_section(path, path_prefix)
            else:
                full_url = f"{domain}{path_prefix}{path}"
                urls.append((title, full_url))

    process_section(sidebar_dict, base_path)
    return urls


def url_to_filename(
    url: str,
    domain: str = "",
    suffix: str = ".md",
    index_name: str = "index",
) -> str:
    """
    将 URL 转换为文件名。

    Args:
        url: 完整 URL
        domain: 域名（用于去除域名部分）
        suffix: 文件后缀
        index_name: 目录索引文件名

    Returns:
        转换后的文件名

    Example:
        >>> url_to_filename('https://example.com/docs/page.html')
        'docs/page.html'
        >>> url_to_filename('https://example.com/docs/')
        'docs/index.html'
    """
    if domain:
        path = url.replace(domain, "")
    else:
        match = re.match(r"https?://[^/]+(.*)", url)
        path = match.group(1) if match else url

    path = path.split("?")[0]
    path = path.rsplit(".html", 1)[0]

    if path.endswith("/index") or path == "":
        path = path.replace("/index", "") or index_name
    elif path.endswith("/"):
        path = path.rstrip("/") + f"/{index_name}"

    if not path.endswith(suffix):
        path = path + suffix

    return path.lstrip("/")


def make_save_callback(
    output_dir: Union[str, Path],
    filename_func: Callable[[str], str] = None,
    domain: str = "",
) -> Callable[[str, str, str], bool]:
    """
    创建保存回调函数。

    Args:
        output_dir: 输出目录
        filename_func: 自定义文件名函数，默认使用 url_to_filename
        domain: 域名

    Returns:
        回调函数 (title, url, markdown) -> bool

    Example:
        >>> callback = make_save_callback('./output')
        >>> callback('Title', 'https://example.com/page.html', '# content')
        True
    """
    output_path = Path(output_dir)
    filename_fn = filename_func or (lambda url: url_to_filename(url, domain))

    def save_callback(title: str, url: str, markdown: str) -> bool:
        if not markdown:
            return False

        try:
            filename = filename_fn(url)
            filepath = output_path / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(markdown, encoding="utf-8")
            return True
        except Exception:
            return False

    return save_callback


def make_progress_callback(
    total: int = None,
    desc: str = "爬取进度",
    unit: str = "page",
) -> Callable[[Dict, int], None]:
    """
    创建进度回调函数。

    Args:
        total: 总数
        desc: 描述
        unit: 单位

    Returns:
        回调函数 (results, total) -> None
    """
    pbar = tqdm(total=total, desc=desc, unit=unit)

    def progress_callback(results: Dict, total: int):
        pbar.total = total
        pbar.n = len(results)
        pbar.refresh()

    return progress_callback


def fix_image_paths(markdown: str, base_url: str) -> str:
    """
    修复 Markdown 中图片路径为绝对路径。

    Args:
        markdown: Markdown 内容
        base_url: 基础 URL

    Returns:
        修复后的 Markdown
    """
    match = re.match(r"(https?://[^/]+)", base_url)
    domain = match.group(1) if match else base_url

    base_path = ""
    if domain in base_url:
        path_part = base_url[len(domain) :]
        if path_part and "/" in path_part:
            base_path = path_part.rsplit("/", 1)[0]

    patterns = [
        (r"!\[([^\]]*)\]\((/[^./][^)]*)\)", r"{}\1".format(domain)),
        (r"!\[([^\]]*)\]\(\./([^)]+)\)", r"{}\1/{}".format(domain, base_path)),
        (r'<img\s+src="(/[^./][^"]+)"', r'<img src="' + domain + r'\1">'),
        (r'<img\s+src="\./([^"]+)"', r'<img src="' + domain + base_path + r'/\1">'),
    ]

    for pattern, replacement in patterns:
        markdown = re.sub(pattern, lambda m: replacement.format(m.group(1)), markdown)

    return markdown


def fix_links(markdown: str, base_url: str) -> str:
    """
    修复 Markdown 中的链接。

    Args:
        markdown: Markdown 内容
        base_url: 基础 URL

    Returns:
        修复后的 Markdown
    """
    match = re.match(r"(https?://[^/]+)", base_url)
    domain = match.group(1) if match else base_url

    base_path = ""
    if domain in base_url:
        path_part = base_url[len(domain) :]
        if path_part and "/" in path_part:
            base_path = path_part.rsplit("/", 1)[0]

    patterns = [
        (r"\[([^\]]*)\]\((/[^./][^)]*)\)", r"[\1](" + domain + r"\2)"),
        (r"\[([^\]]*)\]\(\./([^)]+)\)", r"[\1](" + domain + base_path + r"/\2)"),
    ]

    for pattern, replacement in patterns:
        markdown = re.sub(pattern, replacement, markdown)

    return markdown


def clean_markdown(
    markdown: str,
    remove_selectors: List[str] = None,
    strip_empty_lines: bool = True,
    normalize_whitespace: bool = True,
) -> str:
    """
    清理 Markdown 内容。

    Args:
        markdown: Markdown 内容
        remove_selectors: 要移除的正则表达式列表
        strip_empty_lines: 是否去除空行
        normalize_whitespace: 是否规范化空白字符

    Returns:
        清理后的 Markdown
    """
    if not markdown:
        return ""

    default_remove = [
        r"<script[^>]*>.*?</script>",
        r"<style[^>]*>.*?</style>",
        r"<!--.*?-->",
        r"<nav[^>]*>.*?</nav>",
        r"<header[^>]*>.*?</header>",
        r"<footer[^>]*>.*?</footer>",
        r"<aside[^>]*>.*?</aside>",
    ]

    remove_list = remove_selectors or default_remove
    for pattern in remove_list:
        markdown = re.sub(pattern, "", markdown, flags=re.DOTALL | re.IGNORECASE)

    if strip_empty_lines:
        markdown = re.sub(r"\n\s*\n", "\n\n", markdown)

    if normalize_whitespace:
        markdown = re.sub(r"[ \t]+\n", "\n", markdown)
        markdown = re.sub(r"\n[ \t]+", "\n", markdown)

    return markdown.strip()


def extract_content(tab, selectors: List[str] = None) -> str:
    """
    从页面提取主要内容。

    Args:
        tab: DrissionPage Tab 对象
        selectors: 选择器列表

    Returns:
        HTML 内容
    """
    default_selectors = [
        "main",
        ".main",
        ".main-content",
        ".content-body",
        ".content",
        ".vp-doc",
        ".markdown-body",
        ".docs-content",
        ".documentation-content",
        ".api-content",
        "article",
        "#content",
        "#main-content",
    ]
    select_list = selectors or default_selectors

    for selector in select_list:
        try:
            el = tab.ele(selector, timeout=1)
            if el and len(el.html) > 100:
                return el.html
        except Exception:
            continue
    return tab.html


def extract_title(tab, selectors: List[str] = None) -> Optional[str]:
    """
    从页面提取标题。

    Args:
        tab: DrissionPage Tab 对象
        selectors: 选择器列表

    Returns:
        标题文本
    """
    default_selectors = [
        "h1",
        ".title",
        ".page-title",
        "article h1",
        ".doc-title",
        ".page-header h1",
    ]
    select_list = selectors or default_selectors

    for selector in select_list:
        try:
            el = tab.ele(selector, timeout=1)
            if el and el.text:
                return el.text.strip()
        except Exception:
            continue
    return None


def batch_url_to_filename(urls: List[str], **kwargs) -> List[str]:
    """
    批量转换 URL 为文件名。

    Args:
        urls: URL 列表
        **kwargs: url_to_filename 的其他参数

    Returns:
        文件名列表
    """
    return [url_to_filename(url, **kwargs) for url in urls]


def group_urls_by_domain(urls: List[str]) -> Dict[str, List[str]]:
    """
    按域名分组 URL。

    Args:
        urls: URL 列表

    Returns:
        {域名: [URL列表], ...}
    """
    groups = {}
    for url in urls:
        match = re.match(r"https?://([^/]+)", url)
        if match:
            domain = match.group(1)
            if domain not in groups:
                groups[domain] = []
            groups[domain].append(url)
    return groups


def filter_urls(
    urls: List[str],
    include: List[str] = None,
    exclude: List[str] = None,
) -> List[str]:
    """
    过滤 URL 列表。

    Args:
        urls: URL 列表
        include: 包含关键词列表
        exclude: 排除关键词列表

    Returns:
        过滤后的 URL 列表
    """
    result = urls

    if include:
        result = [url for url in result if any(k in url for k in include)]

    if exclude:
        result = [url for url in result if not any(k in url for k in exclude)]

    return result


def deduplicate_urls(urls: List[str], keep: str = "first") -> List[str]:
    """
    URL 去重。

    Args:
        urls: URL 列表
        keep: 保留策略，"first" 或 "last"

    Returns:
        去重后的 URL 列表
    """
    seen: Dict[str, List[str]] = {}
    for url in urls:
        normalized = url.split("?")[0].rstrip("/")
        if normalized not in seen:
            seen[normalized] = []
        seen[normalized].append(url)

    result = []
    for url_list in seen.values():
        if keep == "first":
            result.append(url_list[0])
        else:
            result.append(url_list[-1])

    return result


def load_crawled_urls(crawl_state_path: Union[str, Path]) -> Set[str]:
    """
    加载已爬取的 URL 列表（用于增量爬取）。

    Args:
        crawl_state_path: 爬取状态文件路径

    Returns:
        已爬取 URL 集合
    """
    path = Path(crawl_state_path)
    if not path.exists():
        return set()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("crawled_urls", []))
    except Exception:
        return set()


def save_crawled_urls(
    urls: Set[str],
    crawl_state_path: Union[str, Path],
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    保存已爬取的 URL 列表（用于增量爬取）。

    Args:
        urls: 已爬取 URL 集合
        crawl_state_path: 爬取状态文件路径
        metadata: 附加元数据

    Returns:
        是否成功
    """
    try:
        path = Path(crawl_state_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "crawled_urls": list(urls),
            "count": len(urls),
        }
        if metadata:
            data["metadata"] = metadata

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True
    except Exception:
        return False


def get_url_hash(url: str) -> str:
    """
    获取 URL 的哈希值。

    Args:
        url: URL 字符串

    Returns:
        哈希值
    """
    normalized = url.split("?")[0].rstrip("/")
    return hashlib.md5(normalized.encode()).hexdigest()


def normalize_url(url: str, domain: str = "") -> str:
    """
    标准化 URL。

    Args:
        url: URL 字符串
        domain: 域名（用于处理相对路径）

    Returns:
        标准化后的 URL
    """
    url = url.strip()

    if url.startswith("//"):
        return "https:" + url

    if url.startswith("/"):
        if domain:
            match = re.match(r"(https?://[^/]+)", domain)
            if match:
                return match.group(1) + url
        return url

    if not url.startswith(("http://", "https://")):
        if domain:
            return domain.rstrip("/") + "/" + url.lstrip("/")
        return url

    return url


def build_url_index(urls: List[tuple], output_dir: Union[str, Path]) -> Path:
    """
    构建 URL 索引文件。

    Args:
        urls: [(标题, URL), ...] 列表
        output_dir: 输出目录

    Returns:
        索引文件路径
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    index = {title: url for title, url in urls}
    index_path = path / "url_index.json"
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return index_path


def load_url_index(index_path: Union[str, Path]) -> Dict[str, str]:
    """
    加载 URL 索引文件。

    Args:
        index_path: 索引文件路径

    Returns:
        {标题: URL} 字典
    """
    path = Path(index_path)
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def estimate_crawl_time(
    url_count: int, avg_time_per_page: float = 3.0, max_workers: int = 5
) -> float:
    """
    估算爬取时间。

    Args:
        url_count: URL 数量
        avg_time_per_page: 每个页面平均耗时（秒）
        max_workers: 并行数

    Returns:
        预估耗时（秒）
    """
    if max_workers <= 0 or url_count <= 0:
        return 0.0
    return (url_count / max_workers) * avg_time_per_page
