"""爬虫核心模块"""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from loguru import logger
from markdownify import markdownify as md

from .config import DEFAULT_CONFIG, CrawlerConfig
from .models import CrawlResult, CrawlStats, CrawlStatus, PageMetadata, ProgressInfo
from .utils import extract_content as _extract_content
from .utils import extract_title as _extract_title
from .utils import fix_image_paths, fix_links, load_crawled_urls, save_crawled_urls

logger.add("crawler.log", rotation="10 MB", retention="7 days", level="WARNING")


class HtmlToMarkdown:
    """HTML 转 Markdown 爬虫类"""

    def __init__(
        self,
        urls: Union[str, List[str]],
        timeout: int = 30,
        wait_until: str = "networkidle",
        headless: bool = True,
        max_workers: int = 5,
        save_callback: Optional[Callable[[str, str, str], bool]] = None,
        content_selectors: Optional[List[str]] = None,
        title_selectors: Optional[List[str]] = None,
        browser_args: Optional[List[str]] = None,
        retry_times: int = 3,
        extract_title: bool = True,
        config: Optional[CrawlerConfig] = None,
        incremental_crawl: bool = False,
        crawl_state_path: Optional[Union[str, Path]] = None,
        skip_existing: bool = False,
    ):
        self.urls = [urls] if isinstance(urls, str) else urls
        self.timeout = timeout
        self.wait_until = wait_until
        self.headless = headless
        self.max_workers = max_workers
        self._retry_times = retry_times
        self._save_callback = save_callback
        self._content_selectors = content_selectors
        self._title_selectors = title_selectors
        self._browser_args = browser_args
        self._extract_title = extract_title
        self._config = config
        self._results: Dict[str, CrawlResult] = {}
        self._browser = None
        self._crawled_urls: set = set()
        self._incremental_crawl = incremental_crawl
        self._crawl_state_path = Path(crawl_state_path) if crawl_state_path else None
        self._skip_existing = skip_existing
        self._stats = CrawlStats()

        from DrissionPage import ChromiumOptions, ChromiumPage

        self._ChromiumOptions = ChromiumOptions
        self._ChromiumPage = ChromiumPage

    @classmethod
    def from_config(cls, urls: Union[str, List[str]], config: CrawlerConfig):
        """从配置创建实例"""
        return cls(
            urls=urls,
            timeout=config.get("timeout", 30),
            wait_until=config.get("wait_until", "networkidle"),
            headless=config.get("headless", True),
            max_workers=config.get("max_workers", 5),
            retry_times=config.get("retry_times", 3),
            extract_title=config.get("extract_title", True),
            content_selectors=config.get("content_selectors"),
            title_selectors=config.get("title_selectors"),
            browser_args=config.get("browser_args"),
            config=config,
        )

    def set_save_callback(self, callback: Callable[[str, str, str], bool]):
        """设置保存回调函数"""
        self._save_callback = callback

    def set_content_selectors(self, selectors: List[str]):
        """设置内容选择器"""
        self._content_selectors = selectors

    def set_title_selectors(self, selectors: List[str]):
        """设置标题选择器"""
        self._title_selectors = selectors

    def get_stats(self) -> CrawlStats:
        """获取爬取统计信息"""
        return self._stats

    def get_progress(self) -> ProgressInfo:
        """获取爬取进度信息"""
        return ProgressInfo(
            current=len(self._results),
            total=len(self.urls),
            results=self._results,
        )

    def _create_browser(self):
        """创建浏览器实例"""
        options = self._ChromiumOptions()
        if self.headless:
            options.headless(True)

        browser_args = self._browser_args or DEFAULT_CONFIG.get("browser_args", [])
        for arg in browser_args:
            options.set_argument(arg)

        return self._ChromiumPage(options)

    def _process_single(
        self, url: str, title: str = None, save_html: bool = False
    ) -> CrawlResult:
        """处理单个 URL

        Args:
            url: URL
            title: 标题
            save_html: 是否保存 HTML
        """
        browser = None
        tab = None
        last_error = None
        extracted_title = None

        metadata = PageMetadata(url=url, title=title, start_time=datetime.now())

        if self._skip_existing and url in self._crawled_urls:
            metadata.status = CrawlStatus.SKIPPED
            metadata.end_time = datetime.now()
            result = CrawlResult(url=url, markdown=None, metadata=metadata)
            self._results[url] = result
            self._stats.skipped += 1
            return result

        for attempt in range(self._retry_times):
            try:
                metadata.retry_count = attempt + 1
                browser = self._create_browser()
                tab = browser.new_tab(url)
                tab.get(url, timeout=self.timeout)
                time.sleep(2)

                if self._extract_title and not title:
                    extracted_title = _extract_title(tab, self._title_selectors)

                html = _extract_content(tab, self._content_selectors)
                markdown = self._convert_to_markdown(html)
                markdown = fix_image_paths(markdown, url)
                markdown = fix_links(markdown, url)

                metadata.status = CrawlStatus.SUCCESS
                metadata.title = extracted_title or title
                metadata.content_length = len(markdown) if markdown else 0
                metadata.end_time = datetime.now()

                result = CrawlResult(
                    url=url,
                    markdown=markdown,
                    metadata=metadata,
                    html=html if save_html else None,
                )

                self._results[url] = result
                self._crawled_urls.add(url)

                if self._save_callback and markdown:
                    self._save_callback(extracted_title or title or url, url, markdown)

                self._close_browser(browser, tab)
                self._stats.success += 1
                return result

            except Exception as e:
                last_error = str(e)
                self._close_browser(browser, tab)
                if attempt < self._retry_times - 1:
                    time.sleep(1)
                    continue

        logger.warning(f"✗ {title or url}: {last_error}")
        metadata.status = CrawlStatus.FAILED
        metadata.error = last_error
        metadata.end_time = datetime.now()

        result = CrawlResult(
            url=url,
            title=title,
            markdown=None,
            metadata=metadata,
        )
        self._results[url] = result
        self._stats.failed += 1
        return result

    def _close_browser(self, browser, tab):
        """安全关闭浏览器"""
        if tab:
            try:
                tab.close()
            except Exception:
                pass
        if browser:
            try:
                browser.quit()
            except Exception:
                pass

    def _convert_to_markdown(self, html: str) -> str:
        """HTML 转 Markdown"""
        return md(html, heading_style="ATX")

    def _load_incremental_state(self):
        """加载增量爬取状态"""
        if self._incremental_crawl and self._crawl_state_path:
            self._crawled_urls = load_crawled_urls(self._crawl_state_path)
            logger.info(f"已加载 {len(self._crawled_urls)} 个已爬取 URL")

    def _save_incremental_state(self):
        """保存增量爬取状态"""
        if self._crawl_state_path:
            save_crawled_urls(
                self._crawled_urls,
                self._crawl_state_path,
                metadata={"last_update": datetime.now().isoformat()},
            )

    def fetch(self, save_html: bool = False) -> Dict[str, Optional[str]]:
        """顺序爬取所有 URL

        Args:
            save_html: 是否保存 HTML

        Returns:
            {url: markdown} 字典
        """
        self._stats.start_time = datetime.now()
        self._load_incremental_state()

        results = {}
        for url in self.urls:
            result = self._process_single(url, save_html=save_html)
            results[result.url] = result.markdown

        self._stats.total = len(self.urls)
        self._stats.end_time = datetime.now()
        self._save_incremental_state()
        return results

    def fetch_parallel(
        self, progress_callback=None, save_html: bool = False
    ) -> Dict[str, Optional[str]]:
        """并行爬取所有 URL

        Args:
            progress_callback: 进度回调
            save_html: 是否保存 HTML

        Returns:
            {url: markdown} 字典
        """
        self._stats.start_time = datetime.now()
        self._load_incremental_state()

        results = {}
        total = len(self.urls)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self._process_single, url, save_html=save_html): url
                for url in self.urls
            }
            for future in as_completed(future_to_url):
                result = future.result()
                results[result.url] = result.markdown
                if progress_callback:
                    progress_callback(results, total)

        self._stats.total = len(self.urls)
        self._stats.end_time = datetime.now()
        self._save_incremental_state()
        return results

    def get_results(self) -> Dict[str, CrawlResult]:
        """获取所有爬取结果"""
        return self._results

    def get_successful(self) -> Dict[str, str]:
        """获取成功的结果"""
        return {
            url: result.markdown
            for url, result in self._results.items()
            if result.markdown
        }

    def get_failed(self) -> Dict[str, str]:
        """获取失败的结果"""
        return {
            url: result.metadata.error
            for url, result in self._results.items()
            if result.metadata.error
        }

    def export_results(
        self, output_path: Union[str, Path], format: str = "json"
    ) -> bool:
        """导出结果

        Args:
            output_path: 输出路径
            format: 格式 ("json", "markdown", "csv")

        Returns:
            是否成功
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if format == "json":
                data = {
                    url: {
                        "title": result.metadata.title,
                        "markdown": result.markdown,
                        "url": result.url,
                        "status": result.metadata.status.value,
                        "error": result.metadata.error,
                        "duration": result.metadata.duration,
                        "content_length": result.metadata.content_length,
                        "retry_count": result.metadata.retry_count,
                    }
                    for url, result in self._results.items()
                }
                path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
                )

            elif format == "markdown":
                lines = ["# 爬取结果报告\n"]
                lines.append(f"- 总数: {len(self._results)}")
                lines.append(f"- 成功: {len(self.get_successful())}")
                lines.append(f"- 失败: {len(self.get_failed())}")
                lines.append("")

                if self.get_failed():
                    lines.append("## 失败列表\n")
                    for url, error in self.get_failed().items():
                        lines.append(f"- [{url}]({url}): {error}")
                    lines.append("")

                path.write_text("\n".join(lines), encoding="utf-8")

            elif format == "csv":
                import csv

                with open(path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ["URL", "标题", "状态", "错误", "耗时(秒)", "内容长度"]
                    )
                    for url, result in self._results.items():
                        writer.writerow(
                            [
                                url,
                                result.metadata.title or "",
                                result.metadata.status.value,
                                result.metadata.error or "",
                                result.metadata.duration or "",
                                result.metadata.content_length,
                            ]
                        )

            return True
        except Exception as e:
            logger.error(f"导出结果失败: {e}")
            return False

    def save_to_dir(self, output_dir: Union[str, Path], file_template: str = None):
        """保存所有结果到目录"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for url, result in self._results.items():
            if not result.markdown:
                continue

            filename = self._url_to_filename(url, file_template)
            filepath = output_path / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(result.markdown, encoding="utf-8")

    def _url_to_filename(self, url: str, template: str = None) -> str:
        """URL 转换为文件名"""
        if template:
            return template

        path = url.split("?")[0]
        if path.endswith("/"):
            path = path + "index.md"
        elif not path.endswith(".md"):
            path = path.rsplit("/", 1)[-1]
            if "." not in path:
                path = path + ".md"

        return path

    def close(self):
        """关闭浏览器"""
        if self._browser:
            try:
                self._browser.quit()
            except Exception:
                pass
            self._browser = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def crawl_urls(
    urls: List[str],
    output_dir: Union[str, Path] = None,
    headless: bool = True,
    max_workers: int = 5,
    timeout: int = 30,
) -> Dict[str, str]:
    """快速爬取 URL 列表"""

    def save_callback(title: str, url: str, markdown: str):
        if output_dir:
            filename = url.split("?")[0].rsplit("/", 1)[-1]
            if not filename.endswith(".md"):
                filename = filename + ".md"
            filepath = Path(output_dir) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(markdown, encoding="utf-8")

    with HtmlToMarkdown(
        urls,
        headless=headless,
        max_workers=max_workers,
        timeout=timeout,
        save_callback=save_callback,
    ) as crawler:
        results = crawler.fetch_parallel()
    return results
