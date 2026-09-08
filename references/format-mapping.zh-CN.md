# 格式映射

中文 | [English](format-mapping.md)

优先使用三种格式都能稳定表达的结构。

| 内容 | Markdown | Notion | 飞书 |
| --- | --- | --- | --- |
| 标题 | `#` 到 `###` | 标题 Block | 标题 Block |
| 无序列表 | `- 项目` | 无序列表项 | 项目符号 Block |
| 有序列表 | `1. 项目` | 有序列表项 | 编号 Block |
| 引用 | `> 内容` | 引用 Block | 引用 Block |
| 代码 | 带语言的围栏代码块 | 代码 Block | 代码 Block |
| 表格 | 管道表格 | 简单表格 | 表格 Block |
| 链接 | Markdown 行内链接 | 富文本链接 | 文本链接 |
| 图片/文件 | 相对路径或 URL | 文件/图片 Block | 媒体/文件 Block |

Notion 数据库、同步 Block、飞书表格、交互组件、评论、权限、页面历史和 @提及无法无损转换为 Markdown。应保留源链接并说明格式损失，不能静默创造替代内容。

Markdown 含本地文件时，以 Markdown 文件所在目录解析相对路径，并通过目标服务的已授权 API 上传。不得在导出的 Markdown 中暴露私密签名 URL。
