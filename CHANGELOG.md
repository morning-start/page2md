# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-02-24

### Changed
- 移除 `collect_urls` 函数，统一使用 `flatten_siderbar` 处理侧边栏 URL 收集
- 优化 API，减少重复函数

## [1.0.0] - 2026-02-24

### Added
- 初始发布版本
- 核心爬虫模块 `HtmlToMarkdown`
- 配置管理模块 (`config.py`)
- 数据模型定义 (`models.py`)
- 工具函数模块 (`utils.py`)
- GitHub Actions 自动发布工作流
- 支持单个或批量 URL 转换
- 使用 DrissionPage 渲染动态网页
- 支持自定义 CSS 选择器
- 支持增量爬取
- 完善的错误处理和重试机制
- 进度回调支持

### Dependencies
- drissionpage >= 4.1.1.2
- loguru >= 0.7.3
- markdownify >= 1.2.2
- tqdm >= 4.67.3
