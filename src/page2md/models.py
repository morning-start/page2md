"""数据类型定义模块"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


class CrawlStatus(Enum):
    """爬取状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PageMetadata:
    """页面元数据"""

    url: str
    title: Optional[str] = None
    status: CrawlStatus = CrawlStatus.PENDING
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    http_status: Optional[int] = None
    content_length: int = 0
    file_path: Optional[Path] = None

    @property
    def duration(self) -> Optional[float]:
        """获取爬取耗时（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.status == CrawlStatus.SUCCESS


@dataclass
class CrawlResult:
    """爬取结果"""

    url: str
    markdown: Optional[str] = None
    metadata: PageMetadata = field(default_factory=lambda: PageMetadata(url=""))
    html: Optional[str] = None

    def __post_init__(self):
        if not self.metadata.url:
            self.metadata.url = self.url


@dataclass
class CrawlStats:
    """爬取统计信息"""

    total: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration(self) -> Optional[float]:
        """总耗时（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total == 0:
            return 0.0
        return self.success / self.total * 100

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": f"{self.success_rate:.2f}%",
            "duration": f"{self.duration:.2f}s" if self.duration else None,
        }


@dataclass
class SidebarItem:
    """侧边栏项"""

    title: str
    path: str
    children: List["SidebarItem"] = field(default_factory=list)
    order: int = 0

    @property
    def is_group(self) -> bool:
        """是否为分组"""
        return len(self.children) > 0

    def flatten(self) -> List[tuple]:
        """展平为 (标题, 路径) 列表"""
        result = []
        if self.is_group:
            for child in self.children:
                result.extend(child.flatten())
        else:
            result.append((self.title, self.path))
        return result


@dataclass
class SaveOptions:
    """保存选项"""

    output_dir: Union[str, Path]
    filename_func: Optional[Callable[[str], str]] = None
    domain: str = ""
    create_index: bool = False
    index_template: str = "{title}"
    overwrite: bool = False
    save_html: bool = False
    html_output_dir: Optional[Union[str, Path]] = None

    def __post_init__(self):
        self.output_dir = Path(self.output_dir) if isinstance(self.output_dir, str) else self.output_dir
        if self.html_output_dir:
            self.html_output_dir = Path(self.html_output_dir) if isinstance(self.html_output_dir, str) else self.html_output_dir


@dataclass
class ProgressInfo:
    """进度信息"""

    current: int = 0
    total: int = 0
    current_url: str = ""
    status: str = "idle"
    results: Dict[str, CrawlResult] = field(default_factory=dict)

    @property
    def percentage(self) -> float:
        """完成百分比"""
        if self.total == 0:
            return 0.0
        return self.current / self.total * 100

    @property
    def success_count(self) -> int:
        """成功数量"""
        return sum(1 for r in self.results.values() if r.metadata.is_success)

    @property
    def failed_count(self) -> int:
        """失败数量"""
        return sum(1 for r in self.results.values() if r.metadata.status == CrawlStatus.FAILED)
