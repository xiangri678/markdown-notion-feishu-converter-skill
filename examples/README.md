# 使用示例 / Examples

## Markdown → Notion

```bash
python3 scripts/markdown_to_notion.py examples/source.example.md \
  --parent-page-id PAGE_ID --dry-run
export NOTION_API_TOKEN='...'
python3 scripts/markdown_to_notion.py examples/source.example.md \
  --parent-page-id PAGE_ID --confirm-write --result /tmp/notion-result.json
```

## Markdown → 飞书

```bash
python3 scripts/feishu_markdown.py import \
  --input examples/source.example.md --title '转换演示'
python3 scripts/feishu_markdown.py import \
  --input examples/source.example.md --title '转换演示' --confirm-write
```

## Notion → Markdown

```bash
export NOTION_API_TOKEN='...'
python3 scripts/notion_to_markdown.py PAGE_ID --output-dir /tmp/notion-export
```

## 飞书 → Markdown

```bash
python3 scripts/feishu_markdown.py export \
  --doc 'https://example.feishu.cn/docx/DOC_TOKEN' \
  --output /tmp/feishu-export.md
```

## Notion → 飞书

先运行 Notion 导出，再导入飞书：

```bash
python3 scripts/notion_to_markdown.py PAGE_ID --output-dir /tmp/notion-export
python3 scripts/feishu_markdown.py import \
  --input /tmp/notion-export/page.md --confirm-write
```

## 飞书 → Notion

```bash
python3 scripts/feishu_markdown.py export --doc DOC_URL --output /tmp/feishu.md
python3 scripts/markdown_to_notion.py /tmp/feishu.md \
  --parent-page-id PAGE_ID --confirm-write
```

## 回读验收

将目标端重新导出的 Markdown 与来源比较：

```bash
python3 scripts/verify_markdown.py examples/source.example.md /tmp/converted.md \
  --report /tmp/conversion-validation.json
```

用 [verification.example.md](verification.example.md) 记录无法无损转换的结构。仓库不保存 Notion 或飞书凭据。

English users can run the same commands or request `$markdown-notion-feishu-converter` with destination read-back verification.
