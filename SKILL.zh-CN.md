# Markdown、Notion、飞书文档转换

中文 | [English](SKILL.md)

在 Markdown、本地文件、Notion 页面和飞书文档之间传输内容。Markdown 作为中间格式。默认执行复制；只有用户明确要求时才删除或替换源文档。

## 选择转换路线

| 来源 | 目标 | 方法 |
| --- | --- | --- |
| Notion | Markdown | 使用 `scripts/notion_to_markdown.py` 或已授权的 Notion 客户端导出 Block |
| Markdown | Notion | 将标题、列表、引用、代码、表格、链接和图片转换为 Notion Block |
| 飞书 | Markdown | 使用 `lark-cli doc read` 或其他已授权客户端读取文档 |
| Markdown | 飞书 | 创建文档、导入 Markdown，然后回读验证 |
| Notion | 飞书 | 先导出 Markdown，规范化后导入飞书 |
| 飞书 | Notion | 先导出 Markdown，规范化后创建 Notion Block |

处理表格、Callout、数据库、附件或嵌套内容前，阅读[格式映射](references/format-mapping.zh-CN.md)。

## 导出 Notion 页面

```bash
export NOTION_API_TOKEN='...'
python3 scripts/notion_to_markdown.py PAGE_ID --output-dir ./exported-page
```

脚本生成 `page.md` 和 `summary.json`。凭据只能来自环境变量或用户已授权的 Connector，不得写入源码、输出文档或日志。

## 安全转换流程

1. 确认来源、目标，以及用户需要复制还是移动。
2. 完整读取来源，包括分页和嵌套 Block。
3. 转换为 Markdown，并在元数据中保留来源 URL 或标识。
4. 遇到不支持的结构时先说明，不要静默压平。
5. 通过已授权客户端创建目标文档。
6. 回读目标，对比标题、段落数、链接、表格、代码块和附件。
7. 返回目标 URL 或路径，并列出有意发生的格式损失。

创建接口返回成功不等于转换完成。执行移动时，只有在回读验证成功且用户明确授权后才能删除来源。
