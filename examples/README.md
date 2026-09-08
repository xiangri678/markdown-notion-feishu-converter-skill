# 使用示例 / Examples

Markdown → Notion：

> 使用 `$markdown-notion-feishu-converter` 把 `examples/source.example.md` 复制到我指定的 Notion 页面。保留标题、待办、链接、代码块和表格；写入前预览，授权后写入并回读验证。

Markdown → 飞书：

> 使用 `$markdown-notion-feishu-converter` 把 `examples/source.example.md` 转成飞书文档。不要删除源文件，完成后返回文档链接和格式损失清单。

Notion → Markdown：

```bash
export NOTION_API_TOKEN='...'
python3 scripts/notion_to_markdown.py PAGE_ID --output-dir /tmp/notion-export
```

用 [verification.example.md](verification.example.md) 记录回读数量和格式损失。Notion/飞书写入由用户已经授权的 Connector 或 CLI 执行，仓库内不保存服务凭据。

English prompts can use the same files and request `$markdown-notion-feishu-converter` with destination read-back verification.
