# page2md 状态设计

## 爬取状态机

### CrawlStatus 状态枚举

```mermaid
stateDiagram-v2
    [*] --> PENDING: 创建任务
    PENDING --> RUNNING: 开始爬取
    RUNNING --> SUCCESS: 爬取成功
    RUNNING --> FAILED: 爬取失败
    RUNNING --> SKIPPED: 跳过(已存在)
    SUCCESS --> [*]
    FAILED --> [*]
    SKIPPED --> [*]
```

### 状态说明

| 状态 | 说明 | 触发条件 |
|------|------|----------|
| PENDING | 等待处理 | 任务创建后 |
| RUNNING | 正在爬取 | 开始爬取时 |
| SUCCESS | 爬取成功 | 成功获取内容 |
| FAILED | 爬取失败 | 发生异常/重试用尽 |
| SKIPPED | 跳过 | 增量爬取时已存在 |

## 增量爬取状态

### 状态管理

```mermaid
sequenceDiagram
    participant U as 用户
    participant C as HtmlToMarkdown
    participant F as 状态文件

    U->>C: 启动增量爬取
    C->>F: load_crawled_urls()
    F-->>C: 返回已爬取URL集合
    
    loop 处理每个URL
        C->>C: 检查URL是否存在
        alt 已存在
            C->>C: 标记为 SKIPPED
        else 不存在
            C->>C: 爬取页面
            C->>C: 标记为 SUCCESS
        end
    end
    
    C->>F: save_crawled_urls()
    F-->>C: 保存成功
    C-->>U: 返回结果
```

### 状态文件格式

```json
{
  "crawled_urls": [
    "https://example.com/page1",
    "https://example.com/page2"
  ],
  "count": 2,
  "metadata": {
    "last_update": "2024-01-01T00:00:00"
  }
}
```

## 统计信息状态

### CrawlStats 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| total | int | 总数 |
| success | int | 成功数 |
| failed | int | 失败数 |
| skipped | int | 跳过数 |
| start_time | datetime | 开始时间 |
| end_time | datetime | 结束时间 |

### 派生属性

| 属性 | 计算方式 |
|------|----------|
| duration | end_time - start_time |
| success_rate | success / total * 100% |
