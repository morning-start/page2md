"""配置管理模块"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, TypedDict, Union


class CrawlerConfig(TypedDict, total=False):
    """爬虫配置类型定义"""

    timeout: int
    wait_until: str
    headless: bool
    max_workers: int
    retry_times: int
    extract_title: bool
    content_selectors: list[str]
    title_selectors: list[str]
    browser_args: list[str]
    output_dir: str
    domain: str


DEFAULT_CONFIG: CrawlerConfig = {
    "timeout": 30,
    "wait_until": "networkidle",
    "headless": True,
    "max_workers": 5,
    "retry_times": 3,
    "extract_title": True,
    "content_selectors": [
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
    ],
    "title_selectors": [
        "h1",
        ".title",
        ".page-title",
        "article h1",
        ".doc-title",
        ".page-header h1",
    ],
    "browser_args": [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-background-networking",
        "--default-apps-disable",
        "--disable-sync",
        "--metrics-recording-only",
        "--mute-audio",
        "--no-first-run",
    ],
}


def load_config(config_path: Union[str, Path]) -> CrawlerConfig:
    """
    从 JSON 文件加载配置。

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典

    Example:
        >>> config = load_config('config.json')
    """
    path = Path(config_path)
    if not path.exists():
        return DEFAULT_CONFIG.copy()

    with open(path, encoding="utf-8") as f:
        user_config = json.load(f)

    return merge_config(DEFAULT_CONFIG, user_config)


def save_config(config: CrawlerConfig, config_path: Union[str, Path]) -> bool:
    """
    保存配置到 JSON 文件。

    Args:
        config: 配置字典
        config_path: 配置文件路径

    Returns:
        是否成功
    """
    try:
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def merge_config(
    default: CrawlerConfig,
    override: Dict[str, Any],
) -> CrawlerConfig:
    """
    合并配置字典。

    Args:
        default: 默认配置
        override: 覆盖配置

    Returns:
        合并后的配置
    """
    result = default.copy()
    for key, value in override.items():
        if value is not None:
            result[key] = value
    return result


def create_config(
    timeout: int = 30,
    headless: bool = True,
    max_workers: int = 5,
    output_dir: str = "./output",
    domain: str = "",
    **kwargs,
) -> CrawlerConfig:
    """
    创建配置字典。

    Args:
        timeout: 超时时间
        headless: 是否无头
        max_workers: 最大并行数
        output_dir: 输出目录
        domain: 默认域名
        **kwargs: 其他配置

    Returns:
        配置字典
    """
    config = DEFAULT_CONFIG.copy()
    config.update(
        {
            "timeout": timeout,
            "headless": headless,
            "max_workers": max_workers,
            "output_dir": output_dir,
            "domain": domain,
        }
    )
    config.update(kwargs)
    return config


def validate_config(config: CrawlerConfig) -> tuple[bool, list[str]]:
    """
    验证配置是否有效。

    Args:
        config: 配置字典

    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []

    if config.get("timeout", 0) <= 0:
        errors.append("timeout must be positive")

    if config.get("max_workers", 0) <= 0:
        errors.append("max_workers must be positive")

    if config.get("retry_times", 0) < 0:
        errors.append("retry_times must be non-negative")

    valid_wait_until = [
        "load",
        "domcontentloaded",
        "networkidle",
        "networkidle0",
        "networkidle2",
    ]
    wait_until = config.get("wait_until", "")
    if wait_until and wait_until not in valid_wait_until:
        errors.append(f"wait_until must be one of {valid_wait_until}")

    return len(errors) == 0, errors


class ConfigManager:
    """配置管理器"""

    def __init__(self, config: Optional[CrawlerConfig] = None):
        """
        初始化配置管理器。

        Args:
            config: 配置字典，默认使用 DEFAULT_CONFIG
        """
        self._config = config or DEFAULT_CONFIG.copy()

    @property
    def config(self) -> CrawlerConfig:
        """获取配置"""
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """设置配置值"""
        self._config[key] = value

    def update(self, config: Dict[str, Any]):
        """更新配置"""
        self._config.update(config)

    def load(self, config_path: Union[str, Path]):
        """从文件加载配置"""
        self._config = load_config(config_path)

    def save(self, config_path: Union[str, Path]) -> bool:
        """保存配置到文件"""
        return save_config(self._config, config_path)

    def validate(self) -> tuple[bool, list[str]]:
        """验证配置"""
        return validate_config(self._config)

    def to_html2markdown(self) -> Dict[str, Any]:
        """转换为 HtmlToMarkdown 构造参数"""
        return {
            "timeout": self._config.get("timeout", 30),
            "wait_until": self._config.get("wait_until", "networkidle"),
            "headless": self._config.get("headless", True),
            "max_workers": self._config.get("max_workers", 5),
            "retry_times": self._config.get("retry_times", 3),
            "extract_title": self._config.get("extract_title", True),
            "content_selectors": self._config.get("content_selectors"),
            "title_selectors": self._config.get("title_selectors"),
            "browser_args": self._config.get("browser_args"),
        }
